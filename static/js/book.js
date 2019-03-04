function startReview() {
	// Focus on review submission form
	document.querySelector('#review-text').focus()
}

function styleStars(e) {
	// Reset star fills
	Array.from(document.querySelectorAll('svg.form-item.star')).forEach(star =>
		star.classList.remove('gold')
	)

	// Fill stars up to selected value
	const selectedVal = e.target.value
	const filteredInputs = Array.from(
		document.querySelectorAll('input.rating')
	).filter(el => el.value <= selectedVal)
	filteredInputs.forEach(input =>
		input.nextElementSibling.firstElementChild.classList.add('gold')
	)
}
