var app = app || {};

app.presentation = function(view, model) {
	let that = {};
	let isSubmitDisabled = false;
	let isMousedown = false;
	let hasJobBoardError = false;

	const defaultErrorMessage = 'An unexpected error occurred. Try resubmitting later!';

	const confirmMessage = 'This will generate a printing protocol for a robot and '
						 +'mark all selected art as in-process. Are you sure?';

	const codeToMessage = {
		'joblist_empty': 'Select a job to manage'
	};

	const emptyJobListMessage = '[Click A Row To Select]';

	const loginFailMessage = "That didn't work. Server says: "

	const notAuthorizedMessage = "Sorry, we haven't cleared you for printing artpieces "
								+ "yet. If you've got a robot and you want to join us in "
								+ "printing bioart just to make people happy, send us an "
								+ "email at ccl.artbot@gmail.com and we'll get you sorted."


	function isEmptyJobList() {
		return model.jobs.noneSelected();
	}

	function enableSubmit() {
		if (!isEmptyJobList()) {
			view.submit.enable();
			view.errorOverlay.hide();
			isSubmitDisabled = false;
		}
	}

	function ui_action_by_id(action, id) {
		if(['select','unselect','hover', 'unhover'].includes(action)){
			let job = view.board.getJob(id);
			view.board[action](job);
		}
	};

	view.board.register.onClick(function(job) {
		if (model.jobs.isSelected(job)) {
			model.jobs.unselect(job);
			ui_action_by_id('unselect', job);
			view.selectedJobList.removeJob(job);
			if(model.jobs.noneSelected()){view.selectedJobList.showPlaceholder();}
		} else {
			model.jobs.select(job);
			img_url = model.jobs.get_img_url(job);
			ui_action_by_id('select', job);
			view.selectedJobList.addJob(job, img_url);
			if (isSubmitDisabled) { enableSubmit(); }
		}
	});

	view.successModal.register.onHide(function() {
		view.board.clear();
		view.selectedJobList.clear();
		model.jobs.clear();
		model.jobs.reset();
		model.jobs.get();
	});

	view.changeLogin.register.onClick(function(){
		view.login.show();
	});

	view.login.register.onSubmit(function(user, password) {
		model.user.login(user, password)
	});
	view.login.register.onChange(function() {
		view.login.reset();
	});
	
	view.labwareSelector.register.onChange(function() {
		let labware = view.labwareSelector.getValue();
		model.labware.select(labware);
	});

	view.submit.register.onClick(function() {
		if (!isSubmitDisabled) {
			isSubmitDisabled = true;
			view.submit.disable();
		}
		if (isEmptyJobList()) {
			view.errorOverlay.show(codeToMessage['joblist_empty']);
			hasJobBoardError = true;
			return;
		}
		model.jobs.submit();
	});

	function createJobBoard(printables) {
		var col = [];
		for (var id_key in printables) {
			delete printables[id_key].art //art not used in display
			for (var key in printables[id_key]) {
				if (col.indexOf(key) === -1) {
					col.push(key);
				}
			}
		}

		view.board.initialize_headers(col);
	
		for (var id_key in printables) {
			job = printables[id_key];
			view.board.add(job);
		}
	}

	function populateLabOptions(labware) {
		for (let i=0; i!=labware.length; ++i) {
			view.labwareSelector.addOption(labware[i]);
		}
	}

	function errorsToMessage(errors) {
		let errorMessage = defaultErrorMessage;
		for (let i=0; i!=errors.length; ++i) {
			let code = errors[i].code;
			if (codeToMessage.hasOwnProperty(code)) {
				errorMessage = codeToMessage[code];
				break;
			}
		}
		return errorMessage;
	}

	let notificationHandlers = {
		'LOGIN_REQUIRED' : function(action) {
			view.login.show()
		}
		,'LOGIN_FAIL' : function(action) {
			view.login.fail(loginFailMessage + action.payload[0].title)
		}
		, 'LOGIN' : function(action) {
			view.login.hide();
			model.user.set_name(action.payload.user);
			model.jobs.get();
			model.labware.get_available();
			view.submit.enable();
		} 
		, 'UPDATE_USER' : function(action) {
			view.userLabel.update(action.payload.name);
		}
		, 'NOT_AUTHORIZED' : function(action) {
			view.warningModal.show(notAuthorizedMessage);
			view.selectedJobList.disable();
			view.submit.disable();
			view.board.clear();
			model.jobs.clear();
		}
		, 'JOB_DATA': function(action) {
			createJobBoard(action.payload.job_data);
		}
		, 'LABWARE_DATA': function(action) {
			populateLabOptions(action.payload.labware_data)
		}
		, 'PRINT_REQ_SUBMIT': function(action) {
			if (action.error) {
				view.warningModal.show(errorsToMessage(action.payload));
			} else {
				view.successModal.update(action.payload.msg, action.payload.procedure_uri)
				view.submissionModal.hide();
				view.successModal.show();
			}
			view.submit.enable();
		}
	};

	that.notify = function(action) {
		if (notificationHandlers.hasOwnProperty(action.type)) {
			notificationHandlers[action.type](action);
		}
	};

	return that;
};
