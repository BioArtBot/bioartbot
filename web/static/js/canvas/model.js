var app = app || {};

app.subject = function() {
	const observers = [];
	return {
		add: function(item) {
			observers.push(item);
		}
		, notifyObservers: function(action) {
			observers.forEach(elem => {
				elem.notify(action);
			});
		}
	}
};

app.model = function() {
	let that = {};
	const subject = this.subject();

	// Inefficient constructor | more idiomitic method doesn't allow for private vars
	function Canvas(size={x: 26, y:26}) {
		let that = {};
		let numOfColoredPixels = 0;
		let coloredPixels = initNulls(size.x);

		function initNulls(size) {
			let nullarray = [];
			for (let i = 0; i != size; ++i) {
				nullarray[i] = null;
			}
			return nullarray;
		}

		that.size = size

		that.isColor = function(pixel, color) {
			if (coloredPixels[pixel.x] == null) {
				return color == null;
			}
			return coloredPixels[pixel.x][pixel.y] == color;
		};

		that.isColorless = function(pixel) {
			return that.isColor(pixel, null);
		};

		that.set = function(pixel, color) {
			if (coloredPixels[pixel.x] == null) {
				coloredPixels[pixel.x] = [];
				for (let i = 0; i != size.y; ++i) {
					coloredPixels[pixel.x][i] = null;
				}
			}
			if (coloredPixels[pixel.x][pixel.y] == null) {
				++numOfColoredPixels;
			}
			coloredPixels[pixel.x][pixel.y] = color;
		};

		that.setAll = function(color) {
			numOfColoredPixels = 0;
			for (let x = 0; x != size.x; ++x) {
				let colors_x = coloredPixels[x] || [];
				for (let y = 0; y != size.y; ++y) {
					++numOfColoredPixels;
					colors_x[y] = color;
				}
				coloredPixels[x] = colors_x;
			}
		};

		that.unset = function(pixel) {
			if (coloredPixels[pixel.x] == null) { return; }
			coloredPixels[pixel.x][pixel.y] = null;
			--numOfColoredPixels;
		};

		function addToColorMap(colorToPixelMap, colors, x) {
			for (let y = 0; y != size.y; ++y) {
				let color = colors[y];
				if (!color) { continue; }
				if (!colorToPixelMap.hasOwnProperty(color)) {
					colorToPixelMap[color] = [];
				}
				// pixels are passed as [y,x]
				colorToPixelMap[color].push([y,x]);
			}
		}

		that.asColorToPixelMap = function() {
			let colorToPixelMap = {};
			for (let x = 0; x != size.x; ++x) {
				let colors_x = coloredPixels[x];
				if (!colors_x) { continue; }
				addToColorMap(colorToPixelMap, colors_x, x);
			}
			return colorToPixelMap;
		};

		that.isEmpty = function() {
			return numOfColoredPixels == 0;
		};

		that.reset = function() {
			numOfColoredPixels = 0;
			coloredPixels = initNulls(size.x);
		};

		return that;
	}

	function Location(){
		let that = {};
		const available = ["ALL"];
		const selected = {};

		that.select = function(selected_location) {
			if(selected_location == "All"){
				delete selected.location;
			} else {
				selected["location"] = selected_location;
			}
		}

		that.load = function(location_data) {
			for (var i = 0; i < location_data.length; i++){
				item = location_data[i];
				available.push(item.name)
			}
		}

		that.available = available;

		that.selected = selected;

		return that;
	}

	let canvas = Canvas();
	let location = Location();

	that.canvas = {
		meta: {
			get: function() {
				request_url = 'artpieces';
				if(location.selected["location"] && location.selected["location"]!='ALL'){
					request_url = request_url + '?location=' + location.selected["location"];
				}
				$.ajax({
					url: request_url
					, type: 'GET'
					, dataType: 'json'
				})
				.done(function(data, textStatus, jqXHR) {
					subject.notifyObservers({
						type: 'CANVAS_META'
						, error: false
						, payload: {
							colors: data.meta.bacterial_colors
						}
					});
				})
				.fail(function(jqXHR, textStatus, errorThrown) {
					subject.notifyObservers({
						type: 'CANVAS_META'
						, error: false
						, payload: {
							colors: data.meta.bacterial_colors
						}
					});
				});
			}
		}
		, set: function(colorId, pixel) {
			if (canvas.isColor(pixel, colorId)) { return; }
			canvas.set(pixel, colorId);
		}
		, setAll: function(colorId) {
			canvas.setAll(colorId);
		}
		, unset: function(pixel) {
			if (canvas.isColorless(pixel)) { return; }
			canvas.unset(pixel);
		}
		, submit: function(email, title) {
			$.ajax({
				url: 'artpieces'
				, type: 'POST'
				, data: JSON.stringify({
					'email': email
					, 'title': title
					, 'art': canvas.asColorToPixelMap()
					, 'canvas_size': canvas.size
				})
				, contentType: 'application/json'
				, dataType: 'json'
			})
			.done(function(data, textStatus, jqXHR) {
				subject.notifyObservers({
					type: 'CANVAS_SUBMIT'
					, error: false
					, payload: data
				});
			})
			.fail(function(jqXHR, textStatus, errorThrown) {
				subject.notifyObservers({
					type: 'CANVAS_SUBMIT'
					, error: true
					, payload: jqXHR.responseJSON.errors
				});
			});
		}
		, reset: function() {
			canvas.reset();
		}
		, isEmpty: function() {
			return canvas.isEmpty();
		}
	};

	that.location = {
		get_available: function() {
			$.ajax({
				url: 'locations'
				, type: 'GET'
				, dataType: 'json'
				, cache: 'false'
			})
			.done(function(data, textStatus, jqXHR) {
				location.load(JSON.parse(data.data));
				let location_data = location.available
				subject.notifyObservers({
					type: 'LOCATION_DATA'
					, error: false
					, payload: {
						location_data
					}
				});
			})
			.fail(function(jqXHR, textStatus, errorThrown) {
				if(jqXHR.status==401){
					subject.notifyObservers({
						type: 'LOGIN_REQUIRED'
					})
				};
				if(jqXHR.status==403){
					subject.notifyObservers({
						type: 'NOT_AUTHORIZED'
					})
				};
			});
		},
		select: function(selected) {
			location.select(selected);
		}
	}

	that.register = function(...args) {
		args.forEach(elem => {
			subject.add(elem);
		});
	};

	return that;
};

