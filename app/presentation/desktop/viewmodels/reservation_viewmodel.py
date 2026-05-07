"""
Reservation ViewModel — bridges ReservationService and ReservationFrame.
Manages date selection state and slot formatting.
"""
from datetime import datetime, timedelta


class ReservationViewModel:
    """Provides reservation data and date-selection state for ReservationFrame."""

    def __init__(self, reservation_service):
        self._svc = reservation_service
        self.selected_date = datetime.now().strftime("%Y-%m-%d")

    # ---- date options ----

    def get_date_options(self) -> list:
        """Get list of (date_str, label, is_today) tuples for the 7-day selector."""
        today = datetime.now()
        options = []
        for i in range(7):
            date = today + timedelta(days=i)
            date_str = date.strftime("%Y-%m-%d")
            if i == 0:
                label = f"今天 {date.strftime('%m/%d')}"
            elif i == 1:
                label = f"明天 {date.strftime('%m/%d')}"
            else:
                weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][date.weekday()]
                label = f"{date.strftime('%m/%d')} {weekday}"
            options.append((date_str, label, i == 0))
        return options

    def select_date(self, date_str: str):
        self.selected_date = date_str

    # ---- reservation CRUD ----

    def get_slots(self) -> list:
        """
        Get time slots for the selected date.
        Returns list of dicts: {hour, time_text, status, user_name, reservation_id}.
        """
        reservations = self._svc.get_reservations(self.selected_date)
        reserved_hours = {}
        for res in reservations:
            for h in range(res['start_hour'], res['end_hour']):
                reserved_hours[h] = res

        current_hour = datetime.now().hour
        today_str = datetime.now().strftime("%Y-%m-%d")
        is_today = (self.selected_date == today_str)

        slots = []
        for hour in range(8, 22):
            time_text = f"{hour:02d}:00 - {hour+1:02d}:00"
            is_past = is_today and hour < current_hour

            if hour in reserved_hours:
                res_info = reserved_hours[hour]
                slots.append({
                    "hour": hour, "time_text": time_text,
                    "status": "reserved",
                    "user_name": res_info['user_name'],
                    "reservation_id": res_info['id'],
                })
            elif is_past:
                slots.append({
                    "hour": hour, "time_text": time_text,
                    "status": "past", "user_name": None, "reservation_id": None,
                })
            else:
                slots.append({
                    "hour": hour, "time_text": time_text,
                    "status": "available", "user_name": None, "reservation_id": None,
                })
        return slots

    def create_reservation(self, name: str, start_hour: int, end_hour: int) -> tuple:
        """Create a reservation. Returns (ok, message, reservation_id)."""
        return self._svc.create_reservation(name, self.selected_date, start_hour, end_hour)

    def cancel_reservation(self, reservation_id: int):
        self._svc.cancel_reservation(reservation_id)
