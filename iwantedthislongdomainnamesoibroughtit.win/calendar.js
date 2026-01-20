document.addEventListener('DOMContentLoaded', function() {
  const calendarEl = document.getElementById('calendar');
  const calendar = new FullCalendar.Calendar(calendarEl, {
    initialView: 'dayGridMonth',
    themeSystem: 'standard',
    headerToolbar: {
      left: 'prev,next today',
      center: 'title',
      right: 'dayGridMonth,timeGridWeek,timeGridDay,listWeek'
    },
    events: '/events.json', // served from the same directory
    eventDidMount: function(info) {
      // Auto color events by keyword
      if (info.event.title.includes("Deadline")) {
        info.el.style.backgroundColor = "crimson";
      } else if (info.event.title.includes("Update")) {
        info.el.style.backgroundColor = "royalblue";
      } else {
        info.el.style.backgroundColor = "seagreen";
      }
    }
  });
  calendar.render();
});
