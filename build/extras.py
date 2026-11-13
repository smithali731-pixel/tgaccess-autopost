"""One-off items outside the 30-day plan. Topics are not used anywhere in content.DAYS."""
EXTRAS = [
 dict(name="2026-11-13-extra-reel", fmt="vert", layout="dark", icon="message-circle-question", tag="FAQ button",
      h="Answers *before they ask*",
      sub="Add your own questions and answers to your bot. Each one becomes a button your members can tap any time.",
      cap="The same five questions, every single day?\n\nPut them in your bot once. Every question becomes a button, and your members get the answer instantly, even while you sleep.\n\ntgaccess.net"),
 dict(name="2026-11-13-extra-post", fmt="post", layout="bold", icon="clipboard-list", tag="Services on order",
      h="Take orders, *deliver in the bot*",
      sub="Buyers fill a short form and pay. You deliver the finished work right inside your bot.",
      cap="Do you offer custom work, like a review, a design or a personal plan?\n\nLet buyers order it from your bot: they fill a short form, pay, and receive the finished file right there in the chat.\n\ntgaccess.net"),
]

EXTRAS.append(dict(name="2026-11-13-bot-post", fmt="post", layout="light", compact=True, icon="bot", tag="Your bot",
    h="What your bot *does for you*",
    grid=[("shopping-cart", "Sells your plans", "Members pick a plan and pay right in the chat"),
          ("door-open", "Lets them in", "The invite is sent the moment they pay"),
          ("user-minus", "Removes expired members", "Nobody stays in for free"),
          ("bell-ring", "Reminds before expiry", "Renewing takes one tap"),
          ("wallet", "Takes 4 ways to pay", "Cards, PayPal, USDT and Telegram Stars"),
          ("layout-dashboard", "Puts you in control", "Plans, members and stats from Telegram")],
    cap="Your bot works for you, so you can focus on your content.\\n\\nIt sells your plans, lets members in the moment they pay, removes them when the subscription ends, reminds them before it runs out, and takes payments by card, PayPal, USDT or Telegram Stars.\\n\\nAnd you manage all of it from inside Telegram.\\n\\nStart free at tgaccess.net"))
