import streamlit as st
from datetime import datetime
import requests
import os

def show_withdrawals(supabase):
    """Render withdrawals management page"""
    st.title("💰 Withdrawal Management")
    st.markdown("*Manual USDT (BEP-20) Processing*")
    
    tab1, tab2, tab3 = st.tabs(["⏳ Pending", "✅ Paid", "❌ Failed"])
    
    with tab1:
        pending = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'pending')\
            .order('requested_at', asc=True)\
            .execute()
        
        if pending.data:
            for w in pending.data:
                user = w['users']
                with st.container():
                    st.markdown(f"### Withdrawal #{w['id']}")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write(f"**User:** {user['first_name'] or user['username']}")
                        st.write(f"**Telegram ID:** `{w['user_id']}`")
                        st.write(f"**Amount:** 💰 **${w['amount']:.2f} USDT**")
                    
                    with col2:
                        st.write(f"**Requested:** {w['requested_at'][:19]}")
                        st.write(f"**Wallet Address:**")
                        st.code(w['wallet_address'], language='text')
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        tx_hash = st.text_input(f"Transaction Hash", placeholder="0x...", key=f"tx_{w['id']}", label_visibility="collapsed")
                    
                    with col2:
                        if st.button(f"✅ Mark as Paid", key=f"pay_{w['id']}", use_container_width=True):
                            supabase.table('withdrawals').update({
                                'status': 'paid',
                                'transaction_hash': tx_hash if tx_hash else None,
                                'paid_at': datetime.now().isoformat()
                            }).eq('id', w['id']).execute()
                            
                            supabase.table('users').update({
                                'total_withdrawn': supabase.raw(f'total_withdrawn + {w["amount"]}')
                            }).eq('telegram_id', w['user_id']).execute()
                            
                            # Notify user
                            bot_token = os.getenv('BOT_TOKEN')
                            notification = f"✅ Withdrawal Completed!\n\n💰 Amount: ${w['amount']:.2f} USDT\n🌐 Network: BEP-20"
                            requests.post(f'https://api.telegram.org/bot{bot_token}/sendMessage', 
                                        json={'chat_id': w['user_id'], 'text': notification})
                            
                            st.success(f"Withdrawal #{w['id']} marked as paid!")
                            st.rerun()
                    
                    with col3:
                        if st.button(f"❌ Reject", key=f"reject_{w['id']}", use_container_width=True):
                            supabase.table('users').update({
                                'balance': supabase.raw(f'balance + {w["amount"]}')
                            }).eq('telegram_id', w['user_id']).execute()
                            
                            supabase.table('withdrawals').update({
                                'status': 'failed'
                            }).eq('id', w['id']).execute()
                            
                            st.rerun()
                    
                    st.divider()
        else:
            st.info("No pending withdrawals 🎉")
    
    with tab2:
        paid = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'paid')\
            .order('paid_at', desc=True)\
            .limit(50)\
            .execute()
        
        if paid.data:
            for w in paid.data:
                st.success(f"#{w['id']}: ${w['amount']:.2f} - {w['users']['first_name']} - Paid on {w['paid_at'][:10]}")
        else:
            st.info("No paid withdrawals")
    
    with tab3:
        failed = supabase.table('withdrawals')\
            .select('*, users(first_name, username)')\
            .eq('status', 'failed')\
            .order('requested_at', desc=True)\
            .limit(50)\
            .execute()
        
        if failed.data:
            for w in failed.data:
                st.error(f"#{w['id']}: ${w['amount']:.2f} - {w['users']['first_name']}")
        else:
            st.info("No failed withdrawals")
