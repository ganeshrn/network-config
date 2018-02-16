# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
import os
import re
import copy
import json
import collections

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.module_utils.network.common.utils import to_list, dict_merge
from ansible.module_utils.network.common.config import NetworkConfig
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.errors import AnsibleError, AnsibleUndefinedVariable, AnsibleFileNotFound

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


def warning(msg):
    if C.ACTION_WARNINGS:
        display.warning(msg)


import q

class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        src = self._task.args['src']
        output = self._task.args['output']
        tags = self._task.args.get('tags')

        try:
            parser = self._find_needle('parsers', src)
        except AnsibleError as exc:
            return {'failed': True, 'msg': to_text(exc)}

        template = self._loader.load_from_file(parser)

        network_config = NetworkConfig(contents=output, indent=3)
        sections = set()
        for entry in network_config.items:
            for p in entry.parents:
                sections.add(p)

        setattr(self, 'network_config', network_config)
        setattr(self, 'sections', sections)

        result['ansible_facts'] = self.parse(output, template, tags)
        return result

    def parse(self, source, template, tags):
        templated_facts = {}
        for entry in template:
            name = entry.get('name')
            entry_tags = entry.get('tags')

            if tags and tags != entry_tags:
                warning('skipping `%s` due to tagging' % name)
                continue

            facts = entry['facts']
            matches = entry['matches']

            loop = entry.get('loop')

            section = entry.get('section')

            context_data = list()

            if section:
                for item in self.sections:
                    if re.match(section, item, re.I):
                        block = self.network_config.get_block_config([item])
                        context_data.append(block)
            else:
                context_data.append(source)

            for data in context_data:
                variables = {'matches': list()}

                for match in matches:
                    match_all = match.pop('match_all', False)
                    pattern = match['pattern']
                    match_var = match.get('match_var')

                    if match_all:
                        res = self.re_matchall(pattern, data)
                    else:
                        res = self.re_search(pattern, data)

                    if match_var:
                        variables[match_var] = res
                    variables['matches'].append(res)

                #if when is not None:
                #    conditional = "{%% if %s %%}True{%% else %%}False{%% endif %%}"
                #    if not self.template(conditional % when, variables):
                #        display.vvvvv("context '%s' skipped due to conditional check failure" % name)
                #        continue

                templated_obj = {}

                if 'loop' in entry:
                    loop_data = self.template(entry['loop'], variables, convert_bare=True)
                    if loop_data:
                        for item in to_list(loop_data):
                            item_data = {'item': item}
                            obj = self.template(entry['facts'], item_data)
                            templated_facts = dict_merge(templated_facts, obj)

                else:
                    obj = self.template(entry['facts'], variables)
                    templated_facts = dict_merge(templated_facts, obj)

        return templated_facts

    def template(self, data, variables, convert_bare=False):

        if isinstance(data, collections.Mapping):
            templated_data = {}
            for key, value in iteritems(data):
                templated_key = self.template(key, variables, convert_bare=convert_bare)
                templated_data[templated_key] = self.template(value, variables, convert_bare=convert_bare)
            return templated_data

        elif isinstance(data, collections.Iterable) and not isinstance(data, string_types):
            return [self.template(i, variables, convert_bare=convert_bare) for i in data]

        else:
            data = data or {}
            tmp_avail_vars = self._templar._available_variables
            self._templar.set_available_variables(variables)
            try:
                resp = self._templar.template(data, convert_bare=convert_bare)
                resp = self._coerce_to_native(resp)
            except AnsibleUndefinedVariable:
                resp = None
                pass
            finally:
                self._templar.set_available_variables(tmp_avail_vars)
            return resp

    def _coerce_to_native(self, value):
        if not isinstance(value, bool):
            try:
                value = int(value)
            except:
                if len(value) == 0:
                    return None
                pass
        return value

    def re_search(self, pattern, value):
        match = re.search(pattern, value, re.M)
        if match:
            return list(match.groups())

    def re_matchall(self, pattern, value):
        return re.findall(pattern, value)

