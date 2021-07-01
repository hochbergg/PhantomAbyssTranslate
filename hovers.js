let glyphShowing = null;
let glyphShowingWidth = null;

let glyphData = {
	showing: null,
	width: null
};

let wallData = {
	showing: null,
	width: null
};

let hubData = {
	showing: null,
	width: null
};

let lastMousePosition = {x: 0, y: 0};

function glyphMouseMove(e) {
	e.target.classList.add('hovered');
	requestAnimationFrame(() => showHover(e, glyphData, 'glyph'));
}

function glyphMouseOut(e) {
	e.target.classList.remove('hovered');
	requestAnimationFrame(() => hideGlyphHover(e, glyphData, 'glyph'));
}

function wallMouseMove(e) {
	e.target.classList.add('hovered');
	requestAnimationFrame(() => showHover(e, wallData, 'wall'));
}

function wallMouseOut(e) {
	e.target.classList.remove('hovered');
	requestAnimationFrame(() => hideGlyphHover(e, wallData, 'wall'));
}

function hubMouseMove(e) {
	e.target.classList.add('hovered');
	requestAnimationFrame(() => showHover(e, hubData, 'hub'));
}

function hubMouseOut(e) {
	e.target.classList.remove('hovered');
	requestAnimationFrame(() => hideGlyphHover(e, hubData, 'hub'));
}

function showHover(e, data, prefix) {
	if ( data.showing !== e.target.dataset.number ) {
		data.showing = e.target.dataset.number;
		const el = document.getElementById(`${prefix}_${data.showing}_hover`);
		data.width = el.offsetWidth;
		el.classList.add('show');
	}
	
	//let position = {x: e.clientX, y: e.clientY};
	const viewportOffset = e.target.getBoundingClientRect();
	let position = {x: viewportOffset.left, y: viewportOffset.bottom };
	if ( position.x !== lastMousePosition.x || position.y !== lastMousePosition.y ) {
		var el = document.getElementById(`${prefix}_${data.showing}_hover`);
		el.style.transform = `translate3d(${position.x-data.width/2+e.target.offsetWidth/2}px,${position.y}px,0)`;
		lastMousePosition = position;	
	}
 }
 
 function hideGlyphHover(e, data, prefix) {
	 if ( data.showing !== null ) {
		  const el = document.getElementById(`${prefix}_${data.showing}_hover`);
		  el.classList.remove('show');
		  data.showing = null;
	  }
  }