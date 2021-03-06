# -*- coding: utf-8 -*-

import time
import datetime

from purchasing.database import db
from purchasing.data.models import (
    Stage, StageProperty, ContractStage, ContractStageActionItem
)
from purchasing.data.contracts import get_one_contract, clone_a_contract

def create_new_stage(stage_data):
    '''Create a new stage.

    Creates a new stage from the passed stage_data
    and returns the created stage object.
    '''
    properties = stage_data.pop('properties', [])
    stage = Stage.create(**stage_data)
    for property in properties:
        property.update({'stage_id': stage.id})
        StageProperty.create(**property)

    return stage

def update_stage(stage_id, stage_data):
    '''Updates stage data.

    Takes an individual stage and updates it with
    the stage data. Returns the updated stage.
    '''
    stage = get_one_stage(stage_id)
    stage.update(**stage_data)
    return stage

def update_stage_property(stage_property_id, property_data):
    '''Updates stage property data.

    Takes a dictionary of stage property data and
    updates the individual property
    '''
    stage_property = StageProperty.query.get(stage_property_id)
    stage_property.update(**property_data)
    return stage_property

def delete_stage(stage_id):
    '''Deletes a stage and any associated properties
    '''
    stage = get_one_stage(stage_id)
    stage.delete()
    return True

def get_one_stage(stage_id):
    '''Takes a stage ID and returns the associated stage object
    '''
    return Stage.query.get(stage_id)

def get_all_stages():
    '''Returns one page's worth of stages.
    '''
    return Stage.query.all()

def log_entered(contract_stage, user):
    return ContractStageActionItem(
        contract_stage_id=contract_stage.id, action_type='reversion',
        taken_by=user.id, taken_at=datetime.datetime.now(),
        action_detail={
            'timestamp': contract_stage.entered.strftime('%Y-%m-%dT%H:%M:%S'),
            'date': contract_stage.entered.strftime('%Y-%m-%d'),
            'type': 'entered', 'label': 'Started work'
        }
    )

def log_exited(contract_stage, user):
    return ContractStageActionItem(
        contract_stage_id=contract_stage.id, action_type='reversion',
        taken_by=user.id, taken_at=datetime.datetime.now(),
        action_detail={
            'timestamp': contract_stage.exited.strftime('%Y-%m-%dT%H:%M:%S'),
            'date': contract_stage.exited.strftime('%Y-%m-%d'),
            'type': 'exited', 'label': 'Completed work'
        }
    )

def log_reopened(contract_stage, user):
    return ContractStageActionItem(
        contract_stage_id=contract_stage.id, action_type='reversion',
        taken_by=user.id, taken_at=datetime.datetime.now(),
        action_detail={
            'timestamp': datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%S'),
            'date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'type': 'reopened', 'label': 'Restarted work'
        }
    )

def _perform_revert(contract, stages, start_idx, end_idx, user):
    '''Bulk removes entry/exit times, and adds events to the action log to signal.

    It should not be possible to have multiple stages with
    entered but not exit. However, we do want to log these events
    appropriately. So, for each stage up the chain until the target
    stage, we strip the enter/exit timestamps, move them into the
    action log, and add a new action for the reversion.
    '''
    stages_to_revert = ContractStage.query.filter(
        ContractStage.contract_id == contract.id,
        ContractStage.stage_id.in_(stages[end_idx:start_idx + 1])
    ).order_by(ContractStage.id).all()

    for stage_idx, contract_stage in enumerate(stages_to_revert):
        db.session.flush()
        db.session.add(log_reopened(contract_stage, user))

        if stage_idx == 0:
            # this is the destination stage. keep the entered open
            db.session.add(log_exited(contract_stage, user))
            db.session.add(log_entered(contract_stage, user))
            contract_stage.entered = datetime.datetime.now()
            contract_stage.exited = None

        elif stage_idx + 1 == len(stages_to_revert):
            contract_stage.entered = None

        else:
            # log everything, fully revert each stage
            db.session.add(log_exited(contract_stage, user))
            db.session.add(log_entered(contract_stage, user))
            contract_stage.full_revert()

    contract.current_stage_id = stages_to_revert[0].stage_id
    return stages_to_revert[0]

def _perform_transition(contract, stages=[], single_enter=True):
    '''Looks up and performs the appropriate exit/enter on two stages

    Stages is a list of integers.
    Single enter is a boolean flag -- true if we are starting
    the process, false if we are completing it.
    '''
    stages_to_transition = ContractStage.query.filter(
        ContractStage.contract_id == contract.id,
        ContractStage.stage_id.in_(stages)
    ).order_by(ContractStage.id).all()

    # exit the current stage
    # enter the new stage
    if len(stages_to_transition) > 1:
        stages_to_transition[0].exit()
        stages_to_transition[1].enter()
        contract.current_stage_id = stages_to_transition[1].stage_id
    else:
        stages_to_transition[0].enter() if single_enter else stages_to_transition[0].exit()
        contract.current_stage_id = stages_to_transition[0].stage_id
    # update the contract's current stage
    return stages_to_transition

def transition_stage(contract_id, destination=None, contract=None, stages=None, user=None):
    '''Transitions a contract from one stage to another

    Stages are organized a bit like a finite state machine. The "flow"
    dictates the order of the states. Because these are linear, we can
    get everything that we need out of the properties of the contract.

    If there is a "destination" stage, then we need to transition all
    the way to that stage, marking everything in-between as complete.

    Otherwise, if the contract doesn't have a current stage, it should
    enter the first stage of its flow. If it does, then it should exit
    that and and move into the next stage. If we are trying to transition
    out of the final stage of the flow, then we need to create a clone
    of the contract.

    Optionally, takes the actual contract object and stages. We can
    always grab the objects if we need them, but they are optional
    to increase speed.
    '''
    # grab the contract
    contract = contract if contract else get_one_contract(contract_id)
    stages = stages if stages else contract.flow.stage_order

    # implement the case where we have a final destination in mind
    if destination:
        current_stage_idx = stages.index(contract.current_stage_id)
        destination_idx = stages.index(destination)

        # if its next, just transition as if it were normal
        if destination_idx == current_stage_idx + 1:
            return transition_stage(contract_id, contract=contract, stages=stages)
        # if it is greater, raise an error. you can't skip stages.
        elif destination_idx > current_stage_idx:
            raise Exception('You cannot skip multiple stages')
        # if it is less, we have to revert stages
        else:
            reversion = _perform_revert(
                contract, stages, current_stage_idx, destination_idx, user
            )
            db.session.commit()
            return reversion, contract, False

    # implement first case -- current stage is none
    elif contract.current_stage_id is None:
        try:
            transition = _perform_transition(
                contract, stages=[stages[0]], single_enter=True
            )
            db.session.commit()
            return transition[0], contract, False
        except Exception:
            db.session.rollback()
            raise

    # implement the second case -- current stage is last stage
    elif contract.current_stage_id == contract.flow.stage_order[-1]:
        # complete the contract
        current_stage_idx = stages.index(contract.current_stage_id)

        try:
            transition = _perform_transition(
                contract, stages=[stages[current_stage_idx]],
                single_enter=False
            )

            new_contract = clone_a_contract(contract)

            return transition[0], new_contract, True
        except Exception:
            raise
            db.session.rollback()

    # implement final case -- transitioning to new stage
    else:
        current_stage_idx = stages.index(contract.current_stage_id)

        try:
            transition = _perform_transition(
                contract, stages=[
                    stages[current_stage_idx], stages[current_stage_idx + 1]
                ]
            )
            db.session.commit()

            return transition[1], contract, False
        except Exception:
            db.session.rollback()
            raise
