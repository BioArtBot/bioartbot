// Global variable to encapsulate app
var app = app || {};

app.init = function() {
	'strict'
	let view = this.view(jQuery);
	let model = this.model();
	let presentation = this.presentation(view, model);

	model.register(presentation);
	model.canvas.meta.get();
	model.location.get_available();
};

$(document).ready(function () {
	if(app.init) {
		app.init();
	}
	console.log(
		'We are an open-source project! '
		+ 'Contributions welcome at https://github.com/cclrobotics/ARTBot'
	);
});
