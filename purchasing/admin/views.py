from flask import url_for, request
from jinja2 import Markup

from purchasing.extensions import admin, db
from purchasing.decorators import AuthMixin, SuperAdminMixin
from wtforms import TextField
from flask_admin.contrib import sqla
from flask_login import current_user
from purchasing.data.models import (
    Stage, StageProperty, Flow, ContractBase, ContractProperty, Company
)
from purchasing.extensions import login_manager
from purchasing.users.models import User, Role

@login_manager.user_loader
def load_user(userid):
    return User.get_by_id(int(userid))

class StageAdmin(AuthMixin, sqla.ModelView):
    inline_models = (StageProperty, )

    form_columns = ['name']

class ContractAdmin(AuthMixin, sqla.ModelView):
    inline_models = (ContractProperty,)

    column_searchable_list = ('description', 'contract_type')

    form_columns = [
        'contract_type', 'description', 'properties',
        'expiration_date', 'current_stage', 'current_flow', 'companies'
    ]

class CompanyAdmin(AuthMixin, sqla.ModelView):

    column_searchable_list = ('company_name',)

    form_columns = [
        'company_name', 'contact_first_name', 'contact_last_name',
        'contact_addr1', 'contact_addr2', 'contact_city',
        'contact_state', 'contact_zip', 'contact_phone',
        'contact_email', 'contracts'
    ]

class FlowAdmin(AuthMixin, sqla.ModelView):
    form_columns = ['flow_name', 'stage_order']

class UserAdmin(AuthMixin, sqla.ModelView):
    form_columns = ['email', 'first_name', 'last_name']

    def is_accessible(self):
        if current_user.is_anonymous():
            return url_for('users.login', next=request.path)
        if current_user.role.name == 'admin':
            return True

class UserRoleAdmin(SuperAdminMixin, sqla.ModelView):
    form_columns = ['email', 'first_name', 'last_name', 'role']

class RoleAdmin(SuperAdminMixin, sqla.ModelView):
    pass

admin.add_view(ContractAdmin(ContractBase, db.session, endpoint='contract'))
admin.add_view(CompanyAdmin(Company, db.session, endpoint='company'))
admin.add_view(StageAdmin(Stage, db.session, endpoint='stage'))
admin.add_view(FlowAdmin(Flow, db.session, endpoint='flow'))
admin.add_view(UserAdmin(User, db.session, name='User', endpoint='user'))
admin.add_view(UserRoleAdmin(User, db.session, name='User w/Roles', endpoint='user-roles'))
admin.add_view(RoleAdmin(Role, db.session, endpoint='role'))