import json
import os
import requests
from http.server import BaseHTTPRequestHandler

# Simple bot token from environment
BOT_TOKEN = os.environ.get('BOT_TOKEN', '')

class handler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Earnify Bot is RUNNING!')
    
    def do_POST(self):
        """Handle Telegram webhook"""
        try:
            # Get the request body
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            if not post_data:
                self.send_response(200)
                self.end_headers()
                return
            
            # Parse the update
            update = json.loads(post_data)
            
            # Extract message info
            message = update.get('message', {})
            chat_id = message.get('chat', {}).get('id')
            text = message.get('text', '')
            first_name = message.get('from', {}).get('first_name', 'User')
            
            # Process commands
            if chat_id and BOT_TOKEN:
                reply = None
                
                if text == '/start':
                    reply = f"""🎉 *Welcome to Earnify, {first_name}!*

Turn simple tasks into USDT rewards!

✨ *How it works:*
• Complete easy tasks
• Earn USDT rewards
• Withdraw to your BEP-20 wallet

📋 *Available Commands:*
/tasks - View available tasks
/balance - Check your balance
/withdraw - Request payout
/daily - Claim daily bonus
/refer - Get referral link
/leaderboard - Top earners
/help - Show all commands

🚀 Start earning now!"""
                
                elif text == '/help':
                    reply = """❓ *Earnify Help*

*Commands:*
/tasks - View available tasks
/balance - Check your balance
/withdraw - Request USDT payout
/daily - Claim daily streak bonus
/refer - Get referral link
/leaderboard - See top earners
/help - Show this message

*Withdrawals:*
• Minimum: $5 USDT
• Network: BEP-20
• Processing: 24-48 hours

Need support? Contact @EarnifySupport"""
                
                elif text == '/balance':
                    reply = f"""💰 *Your Balance*

Current balance: *$0.00 USDT*
Total earned: *$0.00*
Total withdrawn: *$0.00*

💡 Complete tasks to earn rewards!
Send /tasks to start earning."""
                
                elif text == '/tasks':
                    reply = """📋 *Available Tasks*

1. 🌐 *Visit Crypto News* - $0.03
   Visit our partner website (30 seconds)

2. 📺 *Watch Video* - $0.02
   Watch short educational video

3. ✨ *Daily Reward* - $0.05+
   Claim your daily streak bonus

More tasks coming soon!

Send /daily to claim your bonus!"""
                
                elif text == '/daily':
                    reply = """🎁 *Daily Bonus Claimed!*

🔥 Streak: *1 day*
💰 Bonus: *$0.05*

Come back tomorrow for bigger rewards!
Day 7 bonus: $0.15 ✨"""
                
                elif text == '/withdraw':
                    reply = """💸 *Withdraw USDT (BEP-20)*

💰 Minimum withdrawal: *$5 USDT*
🌐 Network: *BEP-20*

📝 *To withdraw:*
1. Send your BEP-20 wallet address
2. Our team will review
3. USDT sent within 24-48 hours

⚠️ *Important:*
• Double-check your address
• Only BEP-20 network supported

*Send your BEP-20 wallet address now:*"""
                
                elif text == '/refer':
                    reply = f"""👥 *Referral Program*

Share and earn 10% forever!

🔗 *Your Link:*
`https://t.me/{os.environ.get('BOT_USERNAME', 'earnify_bot')}?start={chat_id}`

📊 *Your Stats:*
Referrals: 0
Earnings: $0.00

Share your link and start earning!"""
                
                elif text == '/leaderboard':
                    reply = """🏆 *Top Earners Leaderboard*

1. 🥇 Be the first!
2. 🥈 
3. 🥉 

📊 Your Rank: #1
💰 Your Total: $0.00

Complete tasks to climb the ranks!"""
                
                else:
                    # Handle wallet address for withdrawal
                    if text and text.startswith('0x') and len(text) == 42:
                        reply = f"""✅ *Withdrawal Request Submitted!*

💰 Amount: *$0.00 USDT*
📤 Wallet: `{text[:10]}...{text[-6:]}`

⏱️ *Processing time:* 24-48 hours

You'll receive confirmation when sent!"""
                    elif text and not text.startswith('/'):
                        reply = f"""🤔 *Unknown command*

Send /help to see available commands.

Or send your BEP-20 wallet address to withdraw (starts with 0x)."""
                
                # Send response
                if reply:
                    send_url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
                    requests.post(send_url, json={
                        'chat_id': chat_id,
                        'text': reply,
                        'parse_mode': 'Markdown'
                    })
            
            # Always return 200 OK
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok"}).encode())
            
        except Exception as e:
            # Log error (visible in Vercel logs)
            print(f"Error: {e}")
            
            # Still return 200 to Telegram
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')
