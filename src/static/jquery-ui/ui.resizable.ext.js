/*
 * 'this' -> original element
 * 1. argument: browser event
 * 2.argument: ui object
 */

(function($) {

	$.ui.plugin.add("resizable", "containment", {
		
		start: function(e, ui) {
			var o = ui.options, self = ui.instance, el = self.element;
			var oc = o.containment,	ce = (oc instanceof jQuery) ? oc.get(0) : (/parent/.test(oc)) ? el.parent().get(0) : oc;
			if (!ce) return;
			
			if (/document/.test(oc) || oc == document) {
				self.containerOffset = { left: 0, top: 0 };

				self.parentData = { 
					element: $(document), left: 0, top: 0, width: $(document).width(),
					height: $(document).height() || document.body.parentNode.scrollHeight
				};
			}
			
			// i'm a node, so compute top, left, right, bottom
			else{
				self.containerOffset = $(ce).offset(), self.containerSize = { height: $(ce).innerHeight(), width: $(ce).innerWidth() };
			
				var co = self.containerOffset, ch = self.containerSize.height,	cw = self.containerSize.width, 
							width = ($.ui.hasScroll(ce, "left") ? ce.scrollWidth : cw ), height = ($.ui.hasScroll(ce) ? ce.scrollHeight : ch);
			
				self.parentData = { 
					element: ce, left: co.left, top: co.top, width: width, height: height
				};
			}
		},
		
		resize: function(e, ui) {
			var o = ui.options, self = ui.instance, ps = self.containerSize, 
						co = self.containerOffset, cs = self.size, cp = self.position,
							pRatio = o._aspectRatio || e.shiftKey;
			
			if (cp.left < (o.proxy ? co.left : 0)) {
				self.size.width = self.size.width + (o.proxy ? (self.position.left - co.left) : self.position.left);
				if (pRatio) self.size.height = self.size.width * o.aspectRatio;
				self.position.left = o.proxy ? co.left : 0;
			}
			
			if (cp.top < (o.proxy ? co.top : 0)) {
				self.size.height = self.size.height + (o.proxy ? (self.position.top - co.top) : self.position.top);
				if (pRatio) self.size.width = self.size.height / o.aspectRatio;
				self.position.top = o.proxy ? co.top : 0;
			}
			
			var woset = (o.proxy ? self.offset.left - co.left : self.position.left) + self.sizeDiff.width, 
						hoset = (o.proxy ? self.offset.top - co.top : self.position.top) + self.sizeDiff.height;
			
			if (woset + self.size.width >= self.parentData.width) {
				self.size.width = self.parentData.width - woset;
				if (pRatio) self.size.height = self.size.width * o.aspectRatio;
			}
			
			if (hoset + self.size.height >= self.parentData.height) {
				self.size.height = self.parentData.height - hoset;
				if (pRatio) self.size.width = self.size.height / o.aspectRatio;
			}
		}
	});
	
	$.ui.plugin.add("resizable", "grid", {
		
		resize: function(e, ui) {
			var o = ui.options, self =  ui.instance, cs = self.size, os = self.originalSize, op = self.originalPosition, a = o.axis, ratio = o._aspectRatio || e.shiftKey;
			o.grid = typeof o.grid == "number" ? [o.grid, o.grid] : o.grid;
			var ox = Math.round((cs.width - os.width) / o.grid[0]) * o.grid[0], oy = Math.round((cs.height - os.height) / o.grid[1]) * o.grid[1];
			
			if (/^(se|s|e)$/.test(a)) {
				self.size.width = os.width + ox;
				self.size.height = os.height + oy;
			}
			else if (/^(ne)$/.test(a)) {
				self.size.width = os.width + ox;
				self.size.height = os.height + oy;
				self.position.top = op.top - oy;
			}
			else if (/^(sw)$/.test(a)) {
				self.size.width = os.width + ox;
				self.size.height = os.height + oy;
				self.position.left = op.left - ox;
			}
			else {
				self.size.width = os.width + ox;
				self.size.height = os.height + oy;
				self.position.top = op.top - oy;
				self.position.left = op.left - ox;
			}
		}
		
	});
	
	$.ui.plugin.add("resizable", "animate", {
		
		stop: function(e, ui) {
			var o = ui.options, self =  ui.instance;

			var pr = o.proportionallyResize, ista = pr && /textarea/i.test(pr.get(0).nodeName), 
							soffseth = ista && $.ui.hasScroll(pr.get(0), 'left') /* TODO - jump height */ ? 0 : self.sizeDiff.height,
								soffsetw = ista ? 0 : self.sizeDiff.width;
			
			var style = { width: (self.size.width - soffsetw), height: (self.size.height - soffseth) },
						left = parseInt(self.element.css('left'), 10) + (self.position.left - self.originalPosition.left), 
							top = parseInt(self.element.css('top'), 10) + (self.position.top - self.originalPosition.top); 
			
			self.element.animate(
				$.extend(style, { top: top, left: left }),
				{ 
					duration: o.animateDuration || "slow", 
					easing: o.animateEasing || "swing", 
					step: function() {
						if (pr) pr.css({ width: self.element.css('width'), height: self.element.css('height') });
					}
				}
			);
		}
		
	});
	
	$.ui.plugin.add("resizable", "ghost", {
		
		start: function(e, ui) {
			var o = ui.options, self =  ui.instance, pr = o.proportionallyResize, cs = self.size;
			
			if (!pr) self.ghost = self.element.clone();
			else self.ghost = pr.clone();
			
			self.ghost.css(
				{ opacity: .25, display: 'block', position: 'relative', height: cs.height, width: cs.width, margin: 0, left: 0, top: 0 }
			)
			.addClass('ui-resizable-ghost').addClass(typeof o.ghost == 'string' ? o.ghost : '');
			
			self.ghost.appendTo(self.helper);
			
		},
		
		resize: function(e, ui){
			var o = ui.options, self =  ui.instance, pr = o.proportionallyResize;
			
			if (self.ghost) self.ghost.css({ position: 'relative', height: self.size.height, width: self.size.width });
			
		},
		
		stop: function(e, ui){
			var o = ui.options, self =  ui.instance, pr = o.proportionallyResize;
			if (self.ghost && self.helper) self.helper.get(0).removeChild(self.ghost.get(0));
		}
		
	});

})(jQuery);