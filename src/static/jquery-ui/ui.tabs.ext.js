/*
 * Tabs 3 extensions
 *
 * Copyright (c) 2007 Klaus Hartl (stilbuero.de)
 * Dual licensed under the MIT (MIT-LICENSE.txt)
 * and GPL (GPL-LICENSE.txt) licenses.
 *
 * http://docs.jquery.com/UI/TabsExtensions
 */

(function($) {

    /*
     * Rotate
     */
    $.extend($.ui.tabs.prototype, {
        rotation: null,
        rotate: function(ms, continuing) {
            
            continuing = continuing || false;
            
            var self = this, t = this.options.selected;
            
            function start() {
                self.rotation = setInterval(function() {
                    t = ++t < self.$tabs.length ? t : 0;
                    self.select(t);
                }, ms);    
            }
            
            function stop(e) {
                if (!e || e.clientX) { // only in case of a true click
                    clearInterval(self.rotation);
                }
            }
            
            // start interval
            if (ms) {
                start();
                if (!continuing)
                    this.$tabs.bind(this.options.event, stop);
                else
                    this.$tabs.bind(this.options.event, function() {
                        stop();
                        t = self.options.selected;
                        start();
                    });
            }
            // stop interval
            else {
                stop();
                this.$tabs.unbind(this.options.event, stop);
            }
        }
    });

})(jQuery);