// Allow the sidebar to float along with the page while scrolling downwards.

$(document).ready (function() {
  var $sidebar   = $ ('.sidebar_left:not(.noscroll)'),
      $window    = $ (window)
      offset     = $sidebar.offset(),
      topPadding = -10;

  $window.scroll (function () {
    if ($window.scrollTop() > offset.top) {
      $sidebar.stop().animate ({
        marginTop: $window.scrollTop() - offset.top + topPadding
      });
    } else {
      $sidebar.stop().animate ({
        marginTop: 0
      });
    }
  });
});
 
