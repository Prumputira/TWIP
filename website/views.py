from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import Note, Transaction
from . import db
import json
import datetime

views = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST': 
        note = request.form.get('note')

        if len(note) < 1:
            flash('Note is too short!', category='error') 
        else:
            new_note = Note(data=note, user_id=current_user.id)
            db.session.add(new_note)
            db.session.commit()
            flash('Note added!', category='success')

    return render_template("home.html", user=current_user)

@views.route('/delete-note', methods=['POST'])
def delete_note():  
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route('/transactions')
@login_required
def transactions():
    today_date = datetime.date.today().strftime('%Y-%m-%d')
    return render_template("transactions.html", user=current_user, today_date=today_date)

# New transaction API routes
@views.route('/api/transactions', methods=['GET'])
@login_required
def get_transactions():
    try:
        # Get page number from query params, default to 1
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        # Get transactions for the current user, paginated and ordered by date (newest first)
        transactions_query = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc())
        transactions_paginated = transactions_query.paginate(page=page, per_page=per_page, error_out=False)
        
        transactions_list = [t.to_dict() for t in transactions_paginated.items]
        print(f"Found {len(transactions_list)} transactions")
        
        return jsonify({
            'transactions': transactions_list,
            'has_next': transactions_paginated.has_next,
            'total_pages': transactions_paginated.pages,
            'total_items': transactions_paginated.total
        })
    except Exception as e:
        import traceback
        print("Error loading transactions:", str(e))
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 400

@views.route('/api/transactions', methods=['POST'])
@login_required
def create_transaction():
    data = request.json
    print("Received transaction data:", data)
    
    try:
        # Convert date string to date object
        transaction_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        new_transaction = Transaction(
            date=transaction_date,
            type=data['type'],
            category=data['category'],
            subcategory=data.get('subcategory', ''),
            amount=float(data['amount']),
            note=data.get('note', ''),
            user_id=current_user.id
        )
        
        db.session.add(new_transaction)
        db.session.commit()
        
        print("Transaction created successfully:", new_transaction.to_dict())
        return jsonify({
            'success': True, 
            'message': 'Transaction added successfully',
            'transaction': new_transaction.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        import traceback
        print("Error creating transaction:", str(e))
        print(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 400

@views.route('/api/transactions/<int:transaction_id>', methods=['PUT'])
@login_required
def update_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verify this transaction belongs to the current user
    if transaction.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    data = request.json
    
    try:
        # Convert date string to date object
        transaction_date = datetime.datetime.strptime(data['date'], '%Y-%m-%d').date()
        
        transaction.date = transaction_date
        transaction.type = data['type']
        transaction.category = data['category']
        transaction.subcategory = data.get('subcategory', '')
        transaction.amount = float(data['amount'])
        transaction.note = data.get('note', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Transaction updated successfully',
            'transaction': transaction.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@views.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.get_or_404(transaction_id)
    
    # Verify this transaction belongs to the current user
    if transaction.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Transaction deleted successfully'
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

@views.route('/dashboard')
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user, active_page=None)

@views.route('/dashboard/bank-accounts')
@login_required
def bank_accounts():
    return render_template("bank_accounts.html", user=current_user, active_page='bank_accounts')

@views.route('/dashboard/savings-accounts')
@login_required
def savings_accounts():
    return render_template("savings_accounts.html", user=current_user, active_page='savings_accounts')

@views.route('/dashboard/investment-accounts')
@login_required
def investment_accounts():
    return render_template("investment_accounts.html", user=current_user, active_page='investment_accounts')

@views.route('/dashboard/loans')
@login_required
def loans():
    return render_template("loans.html", user=current_user, active_page='loans')

@views.route('/budget')
@login_required
def budget():
    return render_template("budget.html", user=current_user)

@views.route('/styleguide')
@login_required
def styleguide():
    return render_template("styleguide.html", user=current_user)

# Changed function name to avoid duplicate endpoints
@views.route('/ui-styleguide')
@login_required
def ui_styleguide():
    return render_template("styleguide.html", user=current_user)