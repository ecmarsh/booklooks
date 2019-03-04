// Shows confirmation once password is valid length
function showConfirmation(e) {
	var minPasswordLength = 4,
		c = document.querySelector('.form-group.confirmation'),
		p = document.querySelector('#password')
	if (
		e.currentTarget.value.length > minPasswordLength &&
		c.style.display === 'none'
	) {
		// Password length meets requirements & confirmation is hidden
		c.style.display = 'block'
		requestAnimationFrame(function() {
			c.style.opacity = 1
		})
		// Confirmation visible, now monitor changes for confirmation match
		p.removeEventListener('keydown', showConfirmation)
		p.addEventListener('keydown', uiValidate)
		return true
	} else if (
		e.currentTarget.value.length <= minPasswordLength &&
		c.style.display === 'block'
	) {
		// Hide confirmation if visible & password drops below required length
		c.style.display = 'none'
		c.style.opacity = 0
		return true
	}
	return false
}
// Checks if password and confirmation match & provides green or red outline
function uiValidate() {
	var c = document.querySelector('.form-group.confirmation').firstElementChild,
		p = document.querySelector('#password')
	// User started typing confirmation
	if (c.value !== '') {
		// Watch for changes to original password
		p.addEventListener('change', uiValidate)
		if (c.value === p.value) {
			// They match, format green
			c.classList.remove('is-not-valid')
			c.classList.add('is-valid')
			return true
		} else {
			// They don't match, format red
			c.classList.remove('is-valid')
			c.classList.add('is-not-valid')
			return true
		}
	} else if (
		c.classList.contains('is-valid') ||
		c.classList.contains('is-not-valid')
	) {
		// If modifier already added & user deletes their text, return to initial state
		// Using contains in case deletes/cuts with mouse
		;['--is-valid', 'is-not-valid'].forEach(function(clss) {
			c.classList.remove(clss)
		})
		return true
	}
	return false
}
// Validate client-side before submitting form. GET check/
document
	.querySelector('form#register')
	.addEventListener('submit', function(event, flag = false) {
		if (flag === false) {
			event.preventDefault()
			event.stopImmediatePropagation()
		}
		var request = new XMLHttpRequest()
		var usr = document.querySelector('#username').value
		endPoint = '/check'
		urlParams = `?user_name=${usr}`
		request.open('GET', endPoint + urlParams, true)
		request.onload = function() {
			if (request.status >= 200 && request.status < 400) {
				// Success!
				var data = JSON.parse(request.responseText)
				if (data) {
					document.querySelector('form#register').submit(event, true)
					// Bypass stop to default and propgation next submit
					return true
				}
				const usrInput = document.querySelector('#username')
				const inputFeedbck = document.querySelector('.invalid-feedback')
				usrInput.classList.add('is-invalid')
				inputFeedbck.classList.add('is-visible')
				usrInput.addEventListener('keyup', function() {
					inputFeedbck.classList.remove('is-visible')
					usrInput.classList.remove('is-invalid')
				})
				return false
			} else {
				console.log('Server returned an error')
			}
		}
		request.onerror = function() {
			// There was a connection error of some sort
			console.log('Connection error')
		}
		request.send()
	})
