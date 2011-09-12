$(document).ready(function() {
  var cal =$('#calendar');

  cal.fullCalendar({
    theme: true,
    contentHeight: window.innerHeight,
    events: "/calendar/data",
    header: {
      left: '',
      center: 'title',
      right : '',
    }
  })
  function select_view(which)
  {
    $("#view-chooser .view-button").removeClass("selected");
    $("#view-chooser #"+which).addClass("selected");
    var size_factor = 1;
    if (which == "week")
    {
      which = "agendaWeek";
      size_factor = 2;
    }
    if (which == "day")
    {
      which = "agendaDay";
      size_factor = 2;
    }
    cal.fullCalendar("changeView", which);
    cal.fullCalendar('option', 'contentHeight', 
      size_factor*window.innerHeight);
  }

  select_view("month");

  $("#view-chooser #month").bind("touchstart", function() { select_view("month"); } );
  $("#view-chooser #week").bind("touchstart", function() { select_view("week"); } );
  $("#view-chooser #day").bind("touchstart", function() { select_view("day"); } );

  $("#view-nav #backward").bind("touchstart", function() {
    cal.fullCalendar("prev");
  } );
  $("#view-nav #forward").bind("touchstart", function() {
    cal.fullCalendar("next");
  } );
});

