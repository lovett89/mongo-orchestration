#!/usr/bin/python
# coding=utf-8
# Copyright 2012-2014 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys

from bottle import request, run

sys.path.insert(0, '..')

from apps import (error_wrap, get_json, Route,
                  send_result, setup_versioned_routes)
from apps.links import (replica_set_link, all_server_links,
                        all_replica_set_links, all_base_links)
from lib.common import *
from lib.replica_sets import ReplicaSets

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _rs_create(params):
    rs_id = ReplicaSets().create(params)
    result = ReplicaSets().info(rs_id)
    result['links'] = all_replica_set_links(rs_id)
    return result


def _build_member_links(rs_id, member_doc):
    server_id = member_doc['server_id']
    member_id = member_doc['_id']
    member_links = [
        replica_set_link('get-replica-set-member-info', rs_id, member_id),
        replica_set_link('delete-replica-set-member', rs_id, member_id),
        replica_set_link('update-replica-set-member-config',
                         rs_id, member_id)
    ]
    member_links.extend(all_server_links(server_id))
    return member_links


@error_wrap
def rs_create():
    logger.debug("rs_create()")
    data = get_json(request.body)
    data = preset_merge(data, 'replica_sets')
    result = {'replica_set': _rs_create(data)}
    result['links'] = all_base_links(rel_to='add-replica-set')
    return send_result(200, result)


@error_wrap
def rs_list():
    logger.debug("rs_list()")
    replica_sets = []
    for rs_id in ReplicaSets():
        repl_info = {'id': rs_id}
        repl_info['links'] = all_replica_set_links(rs_id, 'get-replica-sets')
        replica_sets.append(repl_info)
    response = {'links': all_base_links(rel_to='get-replica-sets')}
    response['replica_sets'] = replica_sets
    return send_result(200, response)


@error_wrap
def rs_info(rs_id):
    logger.debug("rs_info({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    result = ReplicaSets().info(rs_id)
    result['links'] = all_replica_set_links(rs_id, 'get-replica-set-info')
    return send_result(200, result)


@error_wrap
def rs_command(rs_id):
    logger.debug("rs_command({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    command = get_json(request.body).get('action')
    if command is None:
        raise RequestError('Expected body with an {"action": ...}.')
    result = {
        'command_result': ReplicaSets().command(rs_id, command),
        'links': all_replica_set_links(rs_id, 'replica-set-command')
    }
    result['links'].append(
        replica_set_link('replica-set-command', self_rel=True))
    return send_result(200, result)


@error_wrap
def rs_create_by_id(rs_id):
    logger.debug("rs_create_by_id()")
    data = get_json(request.body)
    data = preset_merge(data, 'replica_sets')
    data['id'] = rs_id
    result = {'replica_set': _rs_create(data)}
    result['replica_set']['links'].append(
        replica_set_link('add-replica-set-by-id', rs_id, self_rel=True)
    )
    result['links'] = all_base_links()
    return send_result(200, result)


@error_wrap
def rs_del(rs_id):
    logger.debug("rs_del({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    result = ReplicaSets().remove(rs_id)
    return send_result(204, result)


@error_wrap
def member_add(rs_id):
    logger.debug("member_add({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    data = get_json(request.body)
    member_id = ReplicaSets().member_add(rs_id, data)
    member_info = ReplicaSets().member_info(rs_id, member_id)
    result = {'member': member_info}
    result['member']['links'] = _build_member_links(rs_id, member_info)
    result['links'] = all_replica_set_links(rs_id, 'add-replica-set-member')
    return send_result(200, result)


@error_wrap
def members(rs_id):
    logger.debug("members({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    member_docs = []
    for member_info in ReplicaSets().members(rs_id):
        member_info['links'] = _build_member_links(rs_id, member_info)
        member_docs.append(member_info)
    result = {
        'members': member_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-members')
    }
    return send_result(200, result)


@error_wrap
def secondaries(rs_id):
    logger.debug("secondaries({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    secondary_docs = []
    for secondary_info in ReplicaSets().secondaries(rs_id):
        secondary_info['links'] = _build_member_links(rs_id, secondary_info)
        secondary_docs.append(secondary_info)
    result = {
        'secondaries': secondary_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-secondaries')
    }
    return send_result(200, result)


@error_wrap
def arbiters(rs_id):
    logger.debug("arbiters({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    arbiter_docs = []
    for arbiter_info in ReplicaSets().arbiters(rs_id):
        arbiter_info['links'] = _build_member_links(rs_id, arbiter_info)
        arbiter_docs.append(arbiter_info)
    result = {
        'arbiters': arbiter_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-arbiters')
    }
    return send_result(200, result)


@error_wrap
def hidden(rs_id):
    logger.debug("hidden({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    hidden_docs = []
    for hidden_info in ReplicaSets().hidden(rs_id):
        hidden_info['links'] = _build_member_links(rs_id, hidden_info)
        hidden_docs.append(hidden_info)
    result = {
        'hidden': hidden_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-hidden-members')
    }
    return send_result(200, result)


@error_wrap
def passives(rs_id):
    logger.debug("passives({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    passive_docs = []
    for passive_info in ReplicaSets().passives(rs_id):
        passive_info['links'] = _build_member_links(rs_id, passive_info)
        passive_docs.append(passive_info)
    result = {
        'passives': passive_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-passive-members')
    }
    return send_result(200, pasives)


@error_wrap
def servers(rs_id):
    logger.debug("hosts({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    server_docs = []
    for server_info in ReplicaSets().servers(rs_id):
        server_info['links'] = _build_member_links(rs_id, server_info)
        server_docs.append(server_info)
    result = {
        'servers': server_docs,
        'links': all_replica_set_links(
            rs_id, rel_to='get-replica-set-servers')
    }
    return send_result(200, result)


@error_wrap
def rs_member_primary(rs_id):
    logger.debug("rs_member_primary({rs_id})".format(**locals()))
    if rs_id not in ReplicaSets():
        return send_result(404)
    primary = ReplicaSets().primary(rs_id)
    result = {'primary': primary}
    result['primary']['links'] = _build_member_links(rs_id, primary)
    result['links'] = all_replica_set_links(
        rs_id, rel_to='get-replica-set-primary')
    return send_result(200, result)


@error_wrap
def member_info(rs_id, member_id):
    logger.debug("member_info({rs_id}, {member_id})".format(**locals()))
    member_id = int(member_id)
    if rs_id not in ReplicaSets():
        return send_result(404)
    member = ReplicaSets().member_info(rs_id, member_id)
    result = {'member': member}
    result['member']['links'] = _build_member_links(rs_id, member)
    result['links'] = all_replica_set_links(rs_id, 'get-replica-set-members')
    return send_result(200, result)


@error_wrap
def member_del(rs_id, member_id):
    logger.debug("member_del({rs_id}), {member_id}".format(**locals()))
    member_id = int(member_id)
    if rs_id not in ReplicaSets():
        return send_result(404)
    result = ReplicaSets().member_del(rs_id, member_id)
    return send_result(204, result)


@error_wrap
def member_update(rs_id, member_id):
    logger.debug("member_update({rs_id}, {member_id})".format(**locals()))
    member_id = int(member_id)
    if rs_id not in ReplicaSets():
        return send_result(404)
    data = get_json(request.body)
    ReplicaSets().member_update(rs_id, member_id, data)
    member = ReplicaSets().member_info(rs_id, member_id)
    result = {'member': member}
    result['member']['links'] = _build_member_links(rs_id, member)
    result['links'] = all_replica_set_links(
        rs_id, 'replica-set-update-member-config')
    return send_result(200, result)


ROUTES = {
    Route('/replica_sets', method='POST'): rs_create,
    Route('/replica_sets', method='GET'): rs_list,
    Route('/replica_sets/<rs_id>', method='GET'): rs_info,
    Route('/replica_sets/<rs_id>', method='POST'): rs_command,
    Route('/replica_sets/<rs_id>', method='PUT'): rs_create_by_id,
    Route('/replica_sets/<rs_id>', method='DELETE'): rs_del,
    Route('/replica_sets/<rs_id>/members', method='POST'): member_add,
    Route('/replica_sets/<rs_id>/members', method='GET'): members,
    Route('/replica_sets/<rs_id>/secondaries', method='GET'): secondaries,
    Route('/replica_sets/<rs_id>/arbiters', method='GET'): arbiters,
    Route('/replica_sets/<rs_id>/hidden', method='GET'): hidden,
    Route('/replica_sets/<rs_id>/passives', method='GET'): passives,
    Route('/replica_sets/<rs_id>/servers', method='GET'): servers,
    Route('/replica_sets/<rs_id>/primary', method='GET'): rs_member_primary,
    Route('/replica_sets/<rs_id>/members/<member_id>',
          method='GET'): member_info,
    Route('/replica_sets/<rs_id>/members/<member_id>',
          method='DELETE'): member_del,
    Route('/replica_sets/<rs_id>/members/<member_id>',
          method='PATCH'): member_update
}

setup_versioned_routes(ROUTES, version='v1')
# Assume v1 if no version is specified.
setup_versioned_routes(ROUTES)


if __name__ == '__main__':
    rs = ReplicaSets()
    rs.set_settings()
    run(host='localhost', port=8889, debug=True, reloader=False)
