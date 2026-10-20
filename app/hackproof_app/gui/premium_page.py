"""My Premium: the native buy + license screens.

Everything the website's buy page does, as first-class app screens
backed by the payments service contract (``payments/``):

- **Buy** — email in → ``POST /api/orders`` → the order's exact
  BTC amount, address, and a wallet QR (rendered by the product's
  own clean-room encoder, identical to the website's) → status
  polling via ``GET /api/orders/<id>`` → on paid, "your key has
  been emailed", and when the service reveals the key to the order
  holder, the key itself with a one-tap save into the app.
- **License key** — a paste-friendly field (Paste is a designed
  flow here, never blocked) verified natively with
  :mod:`hackproof_app.license_keys` — the same checks, and the
  same wording, as the website.

States are designed, never raw: no service connected yet, service
unreachable, order expired, key refused (with the reason in the
product's own words) — each is a calm panel with one clear next
action. No failure ever shows a technical error.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime, timezone

from PySide6.QtCore import QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .. import license_keys, promo, site_bundle
from ..config import OrderRef, SettingsStore
from ..service_client import Order, ServiceClient, ServiceError

POLL_SECONDS = 20

#: Constructor sentinel: "load the promo metadata from the
#: bundled webroot" (the default) vs an explicitly injected
#: metadata dict / None (tests).
_PROMO_UNSET = object()


class _Bridge(QObject):
    """Worker-thread → UI-thread hand-off (Argus's pattern)."""

    done = Signal(object)  # (ok: bool, value)


def _run_async(bridge: _Bridge, fn) -> None:
    def target():
        try:
            bridge.done.emit((True, fn()))
        except BaseException as exc:  # surfaced as a designed state
            bridge.done.emit((False, exc))

    threading.Thread(target=target, daemon=True).start()


def _card(title: str) -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame()
    frame.setObjectName("Card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 12, 18, 12)
    heading = QLabel(title)
    heading.setStyleSheet("font-size: 16px; font-weight: 700;")
    layout.addWidget(heading)
    return frame, layout


def _label(text: str, name: str | None = None, wrap: bool = True) -> QLabel:
    label = QLabel(text)
    if name:
        label.setObjectName(name)
    label.setWordWrap(wrap)
    return label


class PremiumPage(QWidget):
    """The My Premium screen. *client_factory(base_url)* and
    *verify_fn* are injectable seams for tests."""

    license_changed = Signal()

    def __init__(self, store: SettingsStore, manifest: site_bundle.SiteManifest,
                 *, client_factory=None, verify_fn=None, qr_view_factory=None,
                 promo_meta=_PROMO_UNSET,
                 parent=None):
        super().__init__(parent)
        self._store = store
        self._manifest = manifest
        self._client_factory = client_factory or (
            lambda base: ServiceClient(base)
        )
        self._verify = verify_fn or license_keys.verify_license
        self._qr_view_factory = qr_view_factory
        if promo_meta is _PROMO_UNSET:
            promo_meta = promo.load_meta(site_bundle.webroot())
        self._promo_meta = promo_meta
        self._inflight: list[_Bridge] = []
        self._order: Order | None = None
        self._busy = False
        self._promo_busy = False

        root = QVBoxLayout(self)
        root.setContentsMargins(22, 14, 22, 14)
        # Tight vertical rhythm (8px spacing, slimmer card
        # margins): with the promo card added, the column must
        # still fit the designed window height with the payment
        # panel open — the QR holder test guards that budget,
        # and a squeezed layout is how the status line once slid
        # under the QR code.
        root.setSpacing(8)
        title = QLabel("My Premium")
        title.setObjectName("Headline")
        root.addWidget(title)

        self._status_card, status_layout = _card("Premium status")
        self._status_label = _label("")
        status_layout.addWidget(self._status_label)
        self._status_actions = QHBoxLayout()
        self._copy_key_btn = QPushButton("Copy my key")
        self._copy_key_btn.clicked.connect(self._copy_key)
        self._remove_key_btn = QPushButton("Remove key from this app")
        self._remove_key_btn.setObjectName("Danger")
        self._remove_key_btn.clicked.connect(self._remove_key)
        self._status_actions.addWidget(self._copy_key_btn)
        self._status_actions.addWidget(self._remove_key_btn)
        self._status_actions.addStretch(1)
        status_layout.addLayout(self._status_actions)
        root.addWidget(self._status_card)

        self._buy_card, buy_layout = _card("Get premium — $5 in Bitcoin")
        self._buy_note = _label("")
        buy_layout.addWidget(self._buy_note)
        self._email = QLineEdit()
        self._email.setPlaceholderText("you@example.com")
        self._email_label = _label("Email for your license key")
        buy_layout.addWidget(self._email_label)
        buy_layout.addWidget(self._email)
        self._buy_btn = QPushButton("Get payment details")
        self._buy_btn.setObjectName("Primary")
        self._buy_btn.clicked.connect(self.submit_email)
        buy_layout.addWidget(self._buy_btn)
        self._buy_status = _label("", "Dim")
        buy_layout.addWidget(self._buy_status)
        buy_layout.addWidget(self._build_payment_panel())
        root.addWidget(self._buy_card)

        self._key_card, key_layout = _card("I already have a license key")
        key_layout.addWidget(_label(
            "Paste the key from your email. The key is your account — "
            "whoever holds it holds the premium access, so keep it safe."
        ))
        self._key_edit = QPlainTextEdit()
        self._key_edit.setPlaceholderText("Paste your premium license key here")
        self._key_edit.setMaximumHeight(76)
        key_layout.addWidget(self._key_edit)
        self._unlock_btn = QPushButton("Unlock premium")
        self._unlock_btn.setObjectName("Primary")
        self._unlock_btn.clicked.connect(self.submit_key)
        key_layout.addWidget(self._unlock_btn)
        self._key_status = _label("", "Dim")
        key_layout.addWidget(self._key_status)
        root.addWidget(self._key_card)

        self._promo_card, promo_layout = _card("Promo / test code")
        # Slimmer vertical padding than the other cards: this
        # utility card is the column's newest tenant and pays
        # part of its own height budget (see the root note).
        promo_layout.setContentsMargins(18, 8, 18, 8)
        self._promo_explainer = _label(
            "A short code from Sentinel Safeguard — for testing or "
            "a promotion — unlocks premium here. No purchase needed."
        )
        promo_layout.addWidget(self._promo_explainer)
        self._promo_note = _label("", "Dim")
        promo_layout.addWidget(self._promo_note)
        self._promo_edit = QLineEdit()
        self._promo_edit.setPlaceholderText("Enter promo / test code")
        self._promo_edit.setInputMethodHints(
            Qt.InputMethodHint.ImhDigitsOnly
        )
        promo_layout.addWidget(self._promo_edit)
        self._promo_btn = QPushButton("Unlock with code")
        self._promo_btn.setObjectName("Primary")
        self._promo_btn.clicked.connect(self.submit_promo)
        promo_layout.addWidget(self._promo_btn)
        self._promo_status = _label("", "Dim")
        promo_layout.addWidget(self._promo_status)
        root.addWidget(self._promo_card)
        root.addStretch(1)

        self._poll = QTimer(self)
        self._poll.setInterval(POLL_SECONDS * 1000)
        self._poll.timeout.connect(self._poll_order)

        self.refresh()
        self._resume_order()

    # ------------------------------------------------------------ status

    def _dispatch(self, fn, callback) -> None:
        """Run *fn* on a worker thread; call *callback(result)* on
        the UI thread. The bridge is kept alive in _inflight until
        delivery: a queued signal whose sender is destroyed before
        the queue drains is silently dropped (the bridge must
        outlive the round trip, not just the call)."""
        bridge = _Bridge()
        self._inflight.append(bridge)

        def _done(result):
            self._inflight.remove(bridge)
            callback(result)

        bridge.done.connect(_done)
        _run_async(bridge, fn)

    def _client(self) -> ServiceClient:
        return self._client_factory(
            self._store.settings.effective_service_base_url()
        )

    def current_license(self) -> license_keys.LicenseInfo | None:
        """The saved key's verified state, or None (not saved, or
        refused — the refusal itself is shown on the status card)."""
        key = self._store.settings.license_key
        if not key:
            return None
        try:
            return self._verify(
                key,
                self._manifest.public_key_hex or "",
                high_water_ms=self._store.clock_high_water_ms(),
            )
        except license_keys.LicenseError:
            return None

    def refresh(self) -> None:
        """Recompute every state on this page from the store."""
        settings = self._store.settings
        info = self.current_license()
        if info is not None:
            self._store.record_clock_ms(
                max(self._store.clock_high_water_ms(),
                    int(datetime.now(tz=timezone.utc).timestamp() * 1000))
            )
            when = datetime.fromtimestamp(
                info.expiry, tz=timezone.utc
            ).strftime("%B %d, %Y")
            if self._manifest.pack_state == site_bundle.PACK_BUILT:
                closing = (" Your premium lessons and the final exam "
                           "are unlocked.")
            else:
                # The exam works without the pack; the lessons
                # genuinely are not in this edition yet — say so.
                closing = " The final exam is unlocked."
            if promo.is_promo_info(info, self._promo_meta):
                # The saved key is the promo license — label it
                # honestly instead of dressing it as a purchase.
                self._status_label.setText(
                    f"Premium — promo access. Good through {when}."
                    + closing
                )
            else:
                self._status_label.setText(
                    f"Premium is active. License {info.id}, good through "
                    f"{when}." + closing
                )
            self._status_label.setObjectName("Good")
            self._copy_key_btn.setVisible(True)
            self._remove_key_btn.setVisible(True)
            self._buy_card.setVisible(False)
            self._key_card.setVisible(False)
        else:
            self._copy_key_btn.setVisible(False)
            self._remove_key_btn.setVisible(bool(settings.license_key))
            self._buy_card.setVisible(True)
            self._key_card.setVisible(True)
            if settings.license_key:
                try:
                    self._verify(
                        settings.license_key,
                        self._manifest.public_key_hex or "",
                        high_water_ms=self._store.clock_high_water_ms(),
                    )
                except license_keys.LicenseError as exc:
                    self._status_label.setText(exc.user_message)
                    self._status_label.setObjectName("Bad")
                else:  # pragma: no cover - current_license covers it
                    self._status_label.setText("Premium is active.")
            else:
                self._status_label.setText(
                    "You're on the free course. Premium unlocks the full "
                    "course and the final exam."
                )
                self._status_label.setObjectName("Subhead")
        if self._manifest.pack_state == site_bundle.PACK_NOT_BUILT:
            self._status_label.setText(
                self._status_label.text()
                + " Note: this edition's premium lesson pack is still "
                  "being prepared by Sentinel Safeguard — your key and "
                  "purchase stay valid, and the lessons unlock here as "
                  "soon as an edition carrying the pack reaches you."
            )
        # Promo card: pointless once premium is active (any route);
        # in an edition without promo metadata it shows its
        # designed not-active note instead of dead controls.
        promo_active = info is not None
        self._promo_card.setVisible(not promo_active)
        if not promo_active:
            has_meta = self._promo_meta is not None
            self._promo_note.setText(
                "" if has_meta else promo.INACTIVE_MESSAGE
            )
            self._promo_edit.setVisible(has_meta)
            self._promo_btn.setVisible(has_meta)
            # Without metadata the not-active note says it all;
            # the explainer only earns its height when a code
            # can actually be entered.
            self._promo_explainer.setVisible(has_meta)
        # Idle labels stay out of the layout entirely — an empty
        # label still eats line height, and this column's height
        # budget is guarded (see the root layout note).
        self._promo_note.setVisible(bool(self._promo_note.text()))
        self._promo_status.setVisible(bool(self._promo_status.text()))
        self._key_status.setVisible(bool(self._key_status.text()))
        self._update_buy_availability()

    def _update_buy_availability(self) -> None:
        configured = bool(self._store.settings.effective_service_base_url())
        self._email_label.setVisible(configured)
        self._email.setVisible(configured)
        self._buy_btn.setVisible(configured)
        if configured:
            self._buy_note.setText(
                "Send the exact Bitcoin amount shown after checkout — "
                "the exact amount is how your payment is matched to you. "
                "When it confirms on-chain, your license key is generated "
                "and emailed to you automatically."
            )
        else:
            self._buy_note.setText(
                "Buying inside the app isn't switched on in this edition "
                "yet. You can get premium on the HackProof website today — "
                "your key will work here the moment you paste it below."
            )

    # -------------------------------------------------------------- keys

    def _set_key_status(self, style: str, text: str) -> None:
        self._key_status.setObjectName(style)
        self._key_status.setText(text)
        self._key_status.setVisible(bool(text))

    def submit_key(self) -> None:
        text = self._key_edit.toPlainText().strip()
        try:
            info = self._verify(
                text,
                self._manifest.public_key_hex or "",
                high_water_ms=self._store.clock_high_water_ms(),
            )
        except license_keys.LicenseError as exc:
            self._set_key_status("Bad", exc.user_message)
            return
        self._store.settings.license_key = text
        self._store.save()
        self._set_key_status(
            "Good", f"Premium unlocked — welcome in. License {info.id}."
        )
        self._key_edit.clear()
        self.refresh()
        self.license_changed.emit()

    def _copy_key(self) -> None:
        from PySide6.QtWidgets import QApplication

        key = self._store.settings.license_key
        if key:
            QApplication.clipboard().setText(key)
            self._status_label.setText(
                "Your key is copied. Keep it somewhere safe — it is "
                "your account."
            )

    def _remove_key(self) -> None:
        self._store.settings.license_key = ""
        self._store.save()
        self.refresh()
        self.license_changed.emit()

    # ------------------------------------------------------------- promo

    def _set_promo_status(self, style: str, text: str) -> None:
        self._promo_status.setObjectName(style)
        self._promo_status.setText(text)
        self._promo_status.setVisible(bool(text))

    def submit_promo(self) -> None:
        """Promo / test code unlock. The derivation (a 600k-round
        KDF plus signature check) runs on a worker thread; the
        reconstructed license is verified with the same native
        verifier as a pasted key, then stored in the same vault
        slot — from there it is indistinguishable from a purchased
        key (premium state, exam, certificate submission). This
        path never touches the payments service: no order, no
        payment, just the code and the signature."""
        if self._promo_busy:
            return
        settings = self._store.settings
        remaining = promo.throttle_remaining(
            settings.promo_fail_count,
            settings.promo_last_fail_ms,
            int(time.time() * 1000),
        )
        if remaining > 0:
            self._set_promo_status(
                "Bad",
                f"Too many tries — wait about {remaining} seconds "
                "and try again.",
            )
            return
        if self._promo_meta is None:
            self._set_promo_status("Bad", promo.INACTIVE_MESSAGE)
            return
        code = self._promo_edit.text()
        public_key = self._manifest.public_key_hex or ""
        meta = self._promo_meta

        def work():
            key = promo.derive_promo_key(code, meta, public_key)
            info = self._verify(
                key,
                public_key,
                high_water_ms=self._store.clock_high_water_ms(),
            )
            return key, info

        self._promo_busy = True
        self._set_promo_status("Dim", "Checking code…")
        self._dispatch(work, self._promo_done)

    def _promo_done(self, result) -> None:
        self._promo_busy = False
        ok, value = result
        settings = self._store.settings
        if not ok:
            settings.promo_fail_count += 1
            settings.promo_last_fail_ms = int(time.time() * 1000)
            self._store.save()
            if isinstance(value, license_keys.LicenseError):
                message = value.user_message
            else:  # pragma: no cover - defensive, designed wording
                message = ("Something went wrong checking that code. "
                           "Try again.")
            wait = promo.throttle_wait_seconds(settings.promo_fail_count)
            if wait:
                message += (
                    f" Too many tries — wait about {wait} seconds "
                    "before trying again."
                )
            self._set_promo_status("Bad", message)
            return
        key, _info = value
        settings.license_key = key
        settings.promo_fail_count = 0
        settings.promo_last_fail_ms = 0
        self._store.save()
        self._promo_edit.clear()
        self.refresh()
        self.license_changed.emit()

    # ------------------------------------------------------------ buying

    def _build_payment_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 8, 0, 0)
        self._pay_amount = _label("", None)
        self._pay_amount.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #2ee06f;"
        )
        layout.addWidget(self._pay_amount)
        self._pay_address = _label("", "Mono")
        self._pay_address.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        layout.addWidget(self._pay_address)
        row = QHBoxLayout()
        self._copy_addr_btn = QPushButton("Copy address")
        self._copy_addr_btn.clicked.connect(self._copy_address)
        self._check_btn = QPushButton("Check my payment")
        self._check_btn.clicked.connect(self._poll_order_now)
        row.addWidget(self._copy_addr_btn)
        row.addWidget(self._check_btn)
        row.addStretch(1)
        layout.addLayout(row)
        # The QR view is a native browser widget; loose in the
        # layout it can report no height and paint over the
        # status line below it. A fixed-height holder (revealed
        # only once a QR exists) always reserves its space.
        self._qr_holder_widget = QWidget()
        self._qr_holder_widget.setFixedHeight(240)
        self._qr_holder_widget.setVisible(False)
        self._qr_holder = QVBoxLayout(self._qr_holder_widget)
        self._qr_holder.setContentsMargins(0, 4, 0, 4)
        layout.addWidget(self._qr_holder_widget)
        self._pay_status = _label("", "Dim")
        layout.addWidget(self._pay_status)
        self._arrived_key = QPlainTextEdit()
        self._arrived_key.setReadOnly(True)
        self._arrived_key.setMaximumHeight(64)
        self._arrived_key.setVisible(False)
        layout.addWidget(self._arrived_key)
        self._save_arrived_btn = QPushButton("Save this key to HackProof")
        self._save_arrived_btn.setObjectName("Primary")
        self._save_arrived_btn.setVisible(False)
        self._save_arrived_btn.clicked.connect(self._save_arrived_key)
        layout.addWidget(self._save_arrived_btn)
        panel.setVisible(False)
        self._payment_panel = panel
        return panel

    def submit_email(self) -> None:
        email = self._email.text().strip()
        if self._busy:
            return
        self._busy = True
        self._buy_btn.setEnabled(False)
        self._buy_status.setText("Contacting the service…")
        self._dispatch(
            lambda: self._client().create_order(email), self._order_created
        )

    def _order_created(self, result) -> None:
        self._busy = False
        self._buy_btn.setEnabled(True)
        ok, value = result
        if not ok:
            self._buy_status.setObjectName("Bad")
            self._buy_status.setText(
                value.user_message if isinstance(value, ServiceError)
                else "Something went wrong starting checkout. Try again."
            )
            return
        self._buy_status.setObjectName("Dim")
        self._buy_status.setText("")
        self._store.settings.order = OrderRef(
            order_id=value.order_id, email=self._email.text().strip()
        )
        self._store.save()
        self._show_order(value)
        self._poll.start()

    def _resume_order(self) -> None:
        ref = self._store.settings.order
        if not ref.order_id or self.current_license() is not None:
            return
        self._dispatch(
            lambda: self._client().get_order(ref.order_id),
            lambda r: self._order_polled(r, initial=True),
        )

    def _poll_order(self) -> None:
        if self._order is None or self._busy:
            return
        self._poll_order_now()

    def _poll_order_now(self) -> None:
        ref = self._store.settings.order
        if not ref.order_id:
            return
        self._dispatch(
            lambda: self._client().get_order(ref.order_id),
            lambda r: self._order_polled(r, initial=False),
        )

    def _order_polled(self, result, *, initial: bool) -> None:
        ok, value = result
        if not ok:
            if not initial:
                self._pay_status.setText(
                    "Couldn't check just now — your payment is safe; "
                    "HackProof will keep checking."
                )
            return
        self._show_order(value)

    def _show_order(self, order: Order) -> None:
        self._order = order
        self._payment_panel.setVisible(True)
        self._pay_amount.setText(
            f"Send exactly {order.btc_amount_btc} BTC "
            f"({order.btc_amount_sats:,} sats)"
        )
        self._pay_address.setText(order.btc_address)
        self._show_qr(order)
        if order.status == "awaiting_payment":
            self._pay_status.setObjectName("Dim")
            self._pay_status.setText(
                "Waiting for your payment… this page checks on its own. "
                f"Payment window closes {self._expiry_text(order)}."
            )
        elif order.status == "confirming":
            self._pay_status.setObjectName("Dim")
            self._pay_status.setText(
                "Your payment is on the chain and confirming "
                f"({order.confirmations} confirmation"
                f"{'s' if order.confirmations != 1 else ''} so far). "
                "Your key is generated the moment it confirms."
            )
        elif order.status == "paid":
            self._poll.stop()
            email = self._store.settings.order.email or "your email"
            self._pay_status.setObjectName("Good")
            self._pay_status.setText(
                f"Payment confirmed — your license key has been emailed "
                f"to {email}."
            )
            if order.license_key:
                self._pay_status.setText(
                    self._pay_status.text()
                    + " It's also right here — save it to this app:"
                )
                self._arrived_key.setPlainText(order.license_key)
                self._arrived_key.setVisible(True)
                self._save_arrived_btn.setVisible(True)
        elif order.status == "expired":
            self._poll.stop()
            self._pay_status.setObjectName("Bad")
            self._pay_status.setText(
                "This payment window closed before a payment confirmed. "
                "No key was issued for it — start a new checkout above "
                "when you're ready. (If you did send Bitcoin to it, "
                "email Sentinelsafeguard@outlook.com with the "
                "transaction ID and Sentinel will make it right.)"
            )
            self._store.settings.order = OrderRef()
            self._store.save()

    def _expiry_text(self, order: Order) -> str:
        try:
            when = datetime.fromisoformat(
                order.expires_at.replace("Z", "+00:00")
            ).astimezone()
            return "at " + when.strftime("%I:%M %p")
        except ValueError:
            return ""

    def _show_qr(self, order: Order) -> None:
        self._pending_qr_order = order
        if self._qr_view_factory is None:
            return
        if getattr(self, "_qr_view", None) is None:
            view = self._qr_view_factory()
            if view is None:
                return
            self._qr_view = view
            view.setFixedSize(232, 232)
            self._qr_holder.addWidget(view)
            self._qr_holder_widget.setVisible(True)
            view.loadFinished.connect(self._on_qr_loaded)
            from PySide6.QtCore import QUrl

            view.setUrl(QUrl("hackproof://app/_app/qr.html"))
            return
        if getattr(self, "_qr_ready", False):
            self._draw_qr()

    def _on_qr_loaded(self, _ok: bool) -> None:
        self._qr_ready = True
        self._draw_qr()

    def _draw_qr(self) -> None:
        view = getattr(self, "_qr_view", None)
        order = getattr(self, "_pending_qr_order", None)
        if view is None or order is None:
            return
        bip21 = (
            f"bitcoin:{order.btc_address}?amount={order.btc_amount_btc}"
            "&label=HackProof"
        )
        view.page().runJavaScript(
            "renderPaymentQR(" + json.dumps(bip21) + ")"
        )

    def _copy_address(self) -> None:
        from PySide6.QtWidgets import QApplication

        if self._order is not None:
            QApplication.clipboard().setText(self._order.btc_address)
            self._pay_status.setText(
                "Address copied — send exactly the amount shown."
            )

    def _save_arrived_key(self) -> None:
        key = self._arrived_key.toPlainText().strip()
        if not key:
            return
        self._key_edit.setPlainText(key)
        self.submit_key()
        if self.current_license() is not None:
            self._arrived_key.setVisible(False)
            self._save_arrived_btn.setVisible(False)
            self._store.settings.order = OrderRef()
            self._store.save()
