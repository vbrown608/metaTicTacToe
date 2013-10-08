$(document).ready(function() {
	var state = {
		game_id: '{{ game_id}}',
		me: '{{ me }}'
	};

	updateGame = function() {
		$(".board").each( function(i) {
			board = state.metaboard[i];
			$(this).find(".cell").each( function(j) {
				$(this).html(board[j]);
			});
			if (state.all_mini_wins[i] != ' ') {
				$(this).addClass(state.all_mini_wins[i]);
			}
		});
	
		/*for (i = 0; i < 9; i++) {
		  var square = document.getElementById(i);
		  square.innerHTML = state.board[i];
		  if (state.winner != '' && state.winningBoard != '') {
			if (state.winningBoard[i] == state.board[i]) {
			  if (state.winner == state.me) {
				square.style.background = "green";
			  } else {
				square.style.background = "red";
			  }
			} else {
			  square.style.background = "white";
			}
		  }
		}
		*/
		
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
				$(this).click( function() {
					if (isMyMove() && state.metaboard[i][j] == ' ') {
						sendMessage('/move', 'i=' + i, 'j=' + j);
					}
				});
			});
		});
	}
	
	
	highlightSquare = function() {
		$(".cell").hover(
			function() {
				if (state.winner == "" && isMyMove()) {
					$(this).addClass("hover");
				}
			}, 
			function() {
				$(this).removeClass("hover");
			}
		);
	}
  
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
		highlightSquare();
		moveInSquare();
		var i;
		onMessage({data: '{{ initial_message }}'});
	}      

	initialize();
});