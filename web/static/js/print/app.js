// Global variable to encapsulate app
var app = app || {};

app.init = function() {
	'strict'
	let view = this.view(jQuery);
	let model = this.model();
	let presentation = this.presentation(view, model);

	model.register(presentation);
	model.location.get_available();
	model.jobs.get();
	model.labware.get_available();
	model.pipette.get_available();
	model.user.load_name();
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
