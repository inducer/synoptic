$(document).ready(function() {
  $('#calendar').fullCalendar({
    theme: true,
    aspectRatio: 1.8,
    events: "/calendar/data",
    header: {
      left: 'title',
      center: '',
      right: 'month,agendaWeek,agendaDay today prev,next'
    }
  })
});

