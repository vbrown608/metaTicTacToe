$(document).ready(function() {
	var state = {
		game_id: '{{ game_id}}',
		me: '{{ me }}'
	};

	// Update the metaboard.
	updateGame = function() {
		
		$(".board").each( function(i) {
			board = state.metaboard[i];
			$(this).find(".mark").addClass(state.all_mini_wins[i]).html(state.all_mini_wins[i]) // Put big Xs and Os on miniboards.
			$(this).find(".cell").each( function(j) {
				$(this).html(board[j]); // Put little Xs and Os in cells.
			});
			if (isLegalBoard(i) && isMyMove()) { 
				$(this).children().addClass('playable'); // Highlight the miniboard(s) I can play in.
			} else {
				$(this).children().removeClass('playable');
			}
		});
		
		// Hide or display game info.
		var display = {
		  'other-player': 'none',
		  'your-move': 'none',
		  'their-move': 'none',
		  'you-won': 'none',
		  'you-lost': 'none',
		  'metaboard': 'block',
		  'this-game': 'block',
		}; 

		if (!state.userO || state.userO == '') {
		  display['other-player'] = 'block';
		  display['metaboard'] = 'none';
		  display['this-game'] = 'none';
		} else if (state.winner == state.me) {
		  display['you-won'] = 'block';
		} else if (state.winner != '') {
		  display['you-lost'] = 'block';
		} else if (isMyMove()) {
		  display['your-move'] = 'block';
		} else {
		  display['their-move'] = 'block';
		}
		
		// TODO: use jQuery
		for (var label in display) {
		  document.getElementById(label).style.display = display[label];
		}
	};
  
	isMyMove = function() {
		return (state.winner == "") && 
			(state.moveX == (state.userX == state.me));
	}

	myPiece = function() {
		return state.userX == state.me ? 'X' : 'O';
	}
	
	// Check if miniboard is playable.
	isLegalBoard = function(board) {
		console.log(state.last_cell);
		return state.last_cell == board || state.last_cell == -1;
	}
	
	// Check if cell in miniboard is playable.
	isLegalMove = function(board, cell) {
		return isMyMove() && isLegalBoard(board) && state.metaboard[board][cell] == ' ';
	}

	// Send a message to the client with game id
	// Includes two optional params to encode the move: miniboard and cell
	sendMessage = function(path, opt_param, opt_param2) {
		path += '?g=' + state.game_id;
		if (opt_param) {
		  path += '&' + opt_param;
		}
		if (opt_param2) {
		  path += '&' + opt_param2;
		}
		var xhr = new XMLHttpRequest();
		console.log('Sending post request')
		xhr.open('POST', path, true);
		xhr.send();
	};

	moveInSquare = function() {
		$(".board").each( function(i) {
			$(this).find(".cell").each( function(j) {
				// Highlight playable squares on hover.
				$(this).hover( function() {
						if (isLegalMove(i, j)) {
							$(this).addClass('hover'); 
						}
					}, 
					function() {
						$(this).removeClass("hover");
					}
				);
				// Send a message with the move on lick.
				$(this).click( function() {
					if (isLegalMove(i, j)) {
						sendMessage('/move', 'i=' + i, 'j=' + j);
					}
				});
			});
		});
	}
	
	// Highlight playable cells on mouseover.
	highlightSquare = function() {
		$(".board").each( function(i) {
			$(this).find(".cell").each( function(j) {
				$(this).hover( function() {
					if (isLegalMove(i, j)) {
						$(this).addClass('hover');
					}
				});
			});
		});
	}
	
	/*
	highlightSquare = function() {
		$(".cell").hover(
			function() {
				if (isMyMove()) {
					$(this).addClass("hover");
				}
			}, 
			function() {
				$(this).removeClass("hover");
			}
		);
	}
	*/
  
	onOpened = function() {
		sendMessage('/opened');
	};
  
	onMessage = function(m) {
		newState = JSON.parse(m.data);
		state.metaboard = newState.metaboard || state.metaboard;
		state.all_mini_wins = newState.all_mini_wins || state.all_mini_wins;
		state.userX = newState.userX || state.userX;
		state.userO = newState.userO || state.userO;
		state.moveX = newState.moveX;
		state.last_cell = newState.last_cell;
		state.winner = newState.winner || "";
		state.winningBoard = newState.winningBoard || "";
		updateGame();
	}
  
	openChannel = function() {
		var token = '{{ token }}';
		var channel = new goog.appengine.Channel(token);
		var handler = {
			'onopen': onOpened,
			'onmessage': onMessage,
			'onerror': function() {},
			'onclose': function() {}
		};
		var socket = channel.open(handler);
		socket.onopen = onOpened;
		socket.onmessage = onMessage;
	}
  
	initialize = function() {
		openChannel();
		//highlightSquare();
		moveInSquare();
		//var i;
		onMessage({data: '{{ initial_message }}'});
	}      

	initialize();
});