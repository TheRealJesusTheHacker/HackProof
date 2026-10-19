# HackProof — Privacy Policy

Copyright (c) 2026 JesusTheHacker / Sentinel Safeguard LLC. All rights reserved.

## The course collects nothing. That's the selling point.

- **No accounts.** There is nothing to sign up for. Your license key is your account.
- **No tracking.** No analytics, no advertising cookies, no fingerprinting.
- **No network calls in the course or exam pages themselves.** Lessons, license validation, and exam scoring all happen on your device. The separate buy page fetches a BTC price from CoinGecko so it can show you the current $5 equivalent; that is the only automatic network request in the product, and it sends no personal data.
- **Your progress stays on your device.** Scores and license state are never sent to us automatically.

## License keys
- Your license key is validated **offline** on your device using cryptography. Validation never phones home.
- The key is kept **only in your browser's memory**, unless you explicitly check "Remember on this device" — then it's stored in that browser's localStorage, still only on your device. You can wipe it anytime with the "Remove license" button.
- License expiry is checked against **your device's clock**. Keep your clock accurate; a wildly wrong clock can make a valid key look expired (or an expired key look valid, until the next check).

## Purchases
- At checkout you provide an **email address for key delivery**. When your Bitcoin payment is detected on-chain, your license key is generated and emailed to that address automatically. The email is used to deliver your key and to reissue it if you lose it (with your transaction ID as proof of purchase).
- If automatic delivery fails and you contact us, that email conversation contains whatever you put in it — nothing more. We don't sell or share purchase emails, and we don't feed them to anything.

## Exam integrity monitoring
The final exam records **behavioral integrity signals locally in your browser** while an attempt is in progress:

- tab switches and window blurs (leaving the exam tab),
- copy, cut, and paste attempts,
- the time taken to answer each question, and the total exam duration.

When you finish, these signals are summarized into an **integrity verdict (clean / flagged)**. Nothing is uploaded automatically. The summary exists **only inside the certificate code** that is generated when you pass — and it reaches Sentinel Safeguard **only if you choose to submit that code** for countersigning (automatic email delivery or the manual email route). The seller sees the verdict when countersigning and may ask a flagged student to retake the exam. The signals are heuristics — they can flag honest behavior (a notification pulling focus, a fast reader) — and they are never treated as proof on their own.

## Certificate delivery
If you use automatic certificate delivery on the exam page, pressing the button sends your certificate code (your name as entered, your score, the date, your license ID, and the integrity summary above) **and your license key** to our certificate service over HTTPS. The key is required for a technical reason: the code's tamper-proof seal is computed from your license, so the service cannot verify the code is genuine without it — the same reason the manual countersigning tool requires it. With a **clean** integrity verdict, the certificate is countersigned and emailed to you automatically. With a **flagged** verdict, issuance pauses for a human review first — nothing is auto-sent — and the certificate follows once the review is complete. The manual route — emailing the code and your key to us yourself — sends exactly the same information, by email, only when you send it.

One more credential to treat carefully: your **order ID** (shown when you create a purchase order) works like a receipt with your key printed on it — the order-status checker displays your license key to whoever enters the order ID once the order is paid. Keep it private, exactly like the key itself.

## Children
The course is about recognizing scams — useful at any age. Course and exam use involves no data collection from anyone, child or adult.

Questions: Sentinelsafeguard@outlook.com
