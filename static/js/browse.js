window.addEventListener("load", () => {
	alphabet = genCharArray("A", "Z").map(
		char =>
			`<li><a class="char-search" href='/search?q=${char}&browse=true'>${char}</a></li>`
	)
	document
		.querySelector(".alphabet-links")
		.insertAdjacentHTML("afterbegin", alphabet.join(""))
})

function genCharArray(charA, charZ) {
	var a = [],
		i = charA.charCodeAt(0),
		j = charZ.charCodeAt(0)
	for (; i <= j; ++i) {
		a.push(String.fromCharCode(i))
	}
	return a
}
