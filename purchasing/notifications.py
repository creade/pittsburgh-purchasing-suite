# -*- coding: utf-8 -*-

from flask import render_template, current_app
from flask_mail import Message
from purchasing.extensions import mail

def vendor_signup(vendor, categories=[]):
    '''Sends a signup notification to the email associated with a vendor object
    '''
    to_email = vendor.email

    msg_body = render_template('opportunities/emails/signup.html', categories=categories)
    txt_body = render_template('opportunities/emails/signup.txt', categories=categories)

    msg = Message(
        subject='Thank you for signing up!',
        body=txt_body,
        html=msg_body,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[to_email]
    )

    try:
        current_app.logger.debug('SIGNUPTRY | Attempting to send signup message to {}'.format(
            to_email)
        )
        mail.send(msg)
        return True
    except Exception, e:
        current_app.logger.error('SIGNUPFAIL | Attempted signup message to {} failed due to {}'.format(
            to_email, e)
        )
        return False

def wexplorer_feedback(contract, sender, body):
    '''Sends a notification to the configured ADMIN_EMAIL.
    '''
    msg_body = render_template('wexplorer/feedback_email.html', contract=contract, sender=sender, body=body)

    msg = Message(
        subject='Wexplorer contract feedback - ID: {id}, Description: {description}'.format(
            id=contract.id,
            description=contract.description
        ),
        html=msg_body,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[current_app.config['ADMIN_EMAIL']]
    )

    try:
        current_app.logger.debug('WEXFEEDBACK | Attempting to send Wexplorer feedback about ID: {id}'.format(
            id=contract.id)
        )
        mail.send(msg)
        return True
    except Exception, e:
        current_app.logger.error(
            'WEXFEEDBACKERROR | Attempted to send Wexplorer feedback about ID: {id} failed due to {e}'.format(
                id=contract.id, e=e
            )
        )
        return False

def new_contract_autoupdate(contract, sender):
    '''Bulk mails all users following a contract with information about their new contract
    '''
    msg_body = render_template('conductor/emails/new_contract.html', contract=contract)

    with mail.connect() as conn:
        for user in contract.followers:
            msg = Message(
                subject='[Pittsburgh Procurement] A contract you follow has been updated!',
                html=msg_body,
                sender=sender,
                recipients=[user.email]
            )

            conn.send(msg)

def send_conductor_alert(send_to, subject, body, sender):
    '''Trigger email sent from the conductor workflow
    '''
    msg_body = render_template('conductor/emails/email_update.html', body=body)

    msg = Message(
        subject='[Pittsburgh Procurement] {}'.format(subject),
        html=msg_body,
        sender=sender,
        recipients=[send_to]
    )

    mail.send(msg)
    return True
