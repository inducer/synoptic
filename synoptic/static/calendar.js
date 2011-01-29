var SIZE_DECREMENT = 70;

$(document).ready(function() {
  $('#calendar').fullCalendar({
    theme: true,
    contentHeight: window.innerHeight-SIZE_DECREMENT,
    events: "/calendar/data",
    header: {
      left: 'title',
      center: '',
      right: 'month,agendaWeek,agendaDay today prev,next'
    }
  })
  $(window).resize(function() {
    $('#calendar').fullCalendar('option', 'contentHeihgt', 
      window.innerHeight-SIZE_DECREMENT);
  });
});

