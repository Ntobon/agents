# Colsanitas (Colombian prepaid medicine): how booking works

Tested on a Plan Integral contract. Contains no customer data.

## Channels

| Channel | Where | Notes |
| --- | --- | --- |
| Portal | `https://oficinavirtual.colsanitas.com` (from colsanitas.com → Oficina Virtual) | colsanitas.com runs an anti-bot wall (Radware) that blocks embedded browsers; Chrome + extension loads fine. "Mis planes → Mis coberturas" may be empty ("tu contrato no cuenta con información de tu plan"): coverage comes from the contract. "Directorio médico": city + specialty with autocomplete (type, then pick the suggestion). |
| WhatsApp bot | +57 310 310 7676, verified "Colsanitas" account (assistant "María Paula") | Route below |
| Confirmations | `MiCita@colsanitas.com` | Arrive within a minute at the email registered with the insurer, with an `.ics` attachment and "Comprar tu vale" / "Cancelar cita" buttons |

## Bot route

1. First message: share-contact button → **does not load in WhatsApp Web**; accept on the phone.
2. Welcome + channel terms of use.
3. "Tipo y número de documento" → `CC <number>`.
4. "¿Aceptas el envío de información…?" (reminders and commercial) → **NO**.
5. "¿En qué te puedo ayudar?" → free text: "Quiero una cita de <specialty> …".
6. Appointment type: `2` Medicina especializada (1 general, 3 optometry, 4 dentistry, 5 imaging, 6 programs, 7 lab).
7. `1` Agendar citas.
8. Specialty: type the name ("Dermatología", "Medicina interna").
9. `1` Presencial.
10. `1` confirm the registered city.
11. Search by: `1` best availability · `2` date · `3` medical center · `4` doctor name.
12. Slot list (held **5 minutes**) → slot number. Options: `7` more slots · `8` date · `9` center · `10` another doctor.
13. Confirms notification email and phone → `1` Sí. If the email is empty it asks for it: use the one registered with the insurer.
14. Summary with the **appointment code**.
15. "¿Deseas comprar vales?" → `2` No (payment is the user's job).
16. `2` Finalizar. The closing survey can be left unanswered.

**The bot is tied to the ID document of the number writing to it.** It will not book for a beneficiary of the contract: it answers that this goes through "servicios en línea" or the phone line. For a beneficiary there are two paths: the bot from that person's own WhatsApp, or the **Oficina Virtual with the beneficiary's account** (they do the login).

## Oficina Virtual route

Citas médicas → choose the plan (it may also list the public-insurance plan) → Nueva cita → Medicina → Presencial → Por especialidad (type and pick the suggestion) → city → site → "Lo antes posible" + day and time-window filters (Mañana/Tarde/Noche) → Ver agenda (list by day with doctor) → Solicitar → Siguiente → confirm email and phone (prefilled) → Confirmar cita. Appointments booked through the WhatsApp bot **also appear in the portal** (same system) under "Citas agendadas", with cancel and reschedule buttons, so the portal can manage all of them. The portal **shows no appointment code**; the CONFIRMADA status appears under "Citas agendadas". The page is an app that `get_page_text` cannot read: use screenshots.

Searching by center may return only the first doctor with openings (all mornings). For a specific time window, search by doctor name: each has an own schedule.

## Plan Integral rules that affect booking

- Specialist consultations need **no authorization**, only a voucher (orden de compra), one per visit.
- Ultrasound, endoscopy, CT, MRI and other diagnostics **do** need authorization.
- Outpatient drugs are not covered (they go through the EPS).
- Arrive 15 min early with card and ID.
