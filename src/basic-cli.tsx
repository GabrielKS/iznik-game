// import React from "react";
// import ReactDOM, { render } from "react-dom";

const { Component } = React;  // Mysterious fix inspired by https://stackoverflow.com/a/50927095
const { render } = ReactDOM;

const debug = false;

const nullLabel = "-";  // A text label for the "Select:" option in dropdown menus
const labelToNull = (label) => (label === nullLabel ? null : label);
const nullToLabel = (value) => (value === null ? nullLabel : value);
const updateInterval = 1000;

type GameState = {
    stateText: string
}

// enum Tile {
//     FIRST = -1,
//     NONE = 0,
//     AZUL = 1,
//     BLAZE = 2,
//     CRIMSON = 3,
//     DUSK = 4,
//     ETHER = 5
// }

type Tile = "A" | "B" | "C" | "D" | "E"
type StatusType = "note" | "error" | "prompt"

type Move = {
    source: number | null,
    tile: Tile | null,
    dest: number | null
}

type PlayerMove = Move & {
    player: number | null
}

abstract class GameInterface extends Component<{move: Move, handleMoveChange, handleMoveSubmit, input_disabled: any}, {}> {
    constructor(props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.submit_disabled = this.submit_disabled.bind(this);
    }

    abstract handleChange(event): void;

    handleSubmit(event): void {
        this.props.handleMoveSubmit();
        event.preventDefault();
    }

    submit_disabled(): any {
        return (this.props.move.source == null || this.props.move.tile == null || this.props.move.dest == null || this.props.input_disabled == "disabled") ? "disabled" : null;
    }

}

class GraphicalInterface extends GameInterface {

    constructor(props) {
        super(props);
    }

    handleChange(event): void {
        const newMove = Object.assign({}, this.props.move, {[event.target.name]: labelToNull(event.target.value)});
        this.props.handleMoveChange(newMove);
    }

    render() {
        return (
            <form id="graphical-input" onSubmit={this.handleSubmit}>
                <label>Source:
                    <select name="source" id="source" value={nullToLabel(this.props.move.source)} onChange={this.handleChange} disabled={this.props.input_disabled}>
                        <option value={nullLabel}>Select:</option>
                        <option value="0">Bench</option>
                        <option value="1">Batch 1</option>
                        <option value="2">Batch 2</option>
                        <option value="3">Batch 3</option>
                        <option value="4">Batch 4</option>
                        <option value="5">Batch 5</option>
                    </select>
                </label>
                <label>Tile type:
                    <select name="tile" id="tile" value={nullToLabel(this.props.move.tile)} onChange={this.handleChange} disabled={this.props.input_disabled}>
                        <option value={nullLabel}>Select:</option>
                        <option value="A">Azul</option>
                        <option value="B">Blaze</option>
                        <option value="C">Crimson</option>
                        <option value="D">Dusk</option>
                        <option value="E">Ether</option>
                    </select>
                </label>
                <label>Destination:
                    <select name="dest" id="dest" value={nullToLabel(this.props.move.dest)} onChange={this.handleChange} disabled={this.props.input_disabled}>
                        <option value={nullLabel}>Select:</option>
                        <option value="0">Floor</option>
                        <option value="1">Stage 1</option>
                        <option value="2">Stage 2</option>
                        <option value="3">Stage 3</option>
                        <option value="4">Stage 4</option>
                        <option value="5">Stage 5</option>
                    </select>
                </label>
                <label>Play:
                    <input type="submit" value="Submit" disabled={this.submit_disabled()}/>
                </label>
            </form>
        );
    }
}

class CLIInterface extends GameInterface {
    tokenSeparator = " ";

    constructor(props) {
        super(props);
    }

    handleChange(event): void {
        // console.log(event.target.value);
        const newMove = this.commandToMove(event.target.value);
        this.props.handleMoveChange(newMove);
    }

    handleSubmit(event): void {
        this.props.handleMoveSubmit();
        event.preventDefault();
    }

    moveToCommand(move: Move): string {
        let components: string[] = []
        if (move.source != null) {components.push(move.source.toString())}
        else if (move.tile != null || move.dest != null) {components.push(nullLabel)}
        if (move.tile != null) {components.push(move.tile)}
        else if (move.dest != null) {components.push(nullLabel)}
        if (move.dest != null) {components.push(move.dest.toString())}
        return components.join(this.tokenSeparator);

        // return nullToLabel(move.source)+" "+nullToLabel(move.tile)+" "+nullToLabel(move.dest);
    }

    commandToMove(command: string): Move {  // This should be made much prettier.
        const components: string[] = command.replace(/\s/g, "").split("");
        // console.log(components);
        let move: Move = {source: null, tile: null, dest: null};
        if (components.length == 0) {return move};
        let c = components.shift();
        let n = parseInt(c)
        if (n <= 5 && n >= 0) {  // If we can, interpret the first component as the source
            move.source = n;
            if (components.length == 0) {return move};
            c = components.shift().toUpperCase();
        }
        if (["A", "B", "C", "D", "E"].includes(c)) {  // If we can, interpret the second component as the tile
            move.tile = c as Tile;
            if (components.length == 0) {return move};
            c = components.shift();
        }
        n = parseInt(c)
        if (n <= 5 && n >= 0) {  // If we can, interpret the third component as the dest
            move.dest = n;
        }
        return move;
    }

    render() {
        return (
            <form id="cli-input" onSubmit={this.handleSubmit}>
                <label>CLI:
                    <input type="text" id="cli" value={this.moveToCommand(this.props.move)} onChange={this.handleChange}  disabled={this.props.input_disabled}/>
                </label>
                <label>Play:
                    <input type="submit" value="Submit" disabled={this.submit_disabled()}/>
                </label>
            </form>
        );
    }

}

class StatusMsg extends Component<{msg: string, type: StatusType}, {}> {
    constructor(props) {
        super(props);
    }

    render() {
        return (
            <div id="status-line">Status:{" "}
            <span id="status-msg" className={"status-"+this.props.type}>{this.props.msg}</span>
            </div>
        );
    }
}

class Game extends Component<{}, {gameState: GameState, stagedMove: Move, myPlayer: number | null, intervalID: number | null, status: string, statusType: StatusType}> {
    constructor(props) {
        super(props);
        this.state = {
            gameState: {
                stateText: "Not yet updated…"
            },
            stagedMove: {source: null, tile: null, dest: null},
            myPlayer: null,
            intervalID: null,
            status: "Please select your Player ID above",
            statusType: "prompt"
        };
        this.handleMoveChange = this.handleMoveChange.bind(this);
        this.handleMoveSubmit = this.handleMoveSubmit.bind(this);
        this.handlePlayerChange = this.handlePlayerChange.bind(this);
        this.pollServerManually = this.pollServerManually.bind(this);
        this.pollServer = this.pollServer.bind(this);
        this.pollServerPlayer = this.pollServerPlayer.bind(this);
        this.receiveState = this.receiveState.bind(this);
        this.moveSent = this.moveSent.bind(this);
    }

    pollServerManually(): void {
        this.setState({
            gameState: {
                stateText: "Contacting server…"
            }
        });
        this.pollServer();
    }

    pollServer(): void {
        this.pollServerPlayer(this.state.myPlayer)
    }

    pollServerPlayer(player: number | null): void {
        const xhttp = new XMLHttpRequest();
        const cf = this.receiveState;
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                cf(this);
            }
        };
        xhttp.open("POST", "/basic-cli/play", true)  // But I don't think POST is what I want — I'm not altering server state
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.send(JSON.stringify({
            requestType: "stateText",
            player: player
        }));
    }

    receiveState(xhttp) {
        const response = JSON.parse(xhttp.response)
        this.setState({
            gameState: {
                stateText: response.stateText
            },
            status: response.status,
            statusType: response.statusType
        });
    }
    
    sendMove(move: Move): void {
        const playerMove: PlayerMove = Object.assign({}, {player: this.state.myPlayer}, move)
        const xhttp = new XMLHttpRequest();
        const cf = this.moveSent;
        xhttp.onreadystatechange = function() {
            if (this.readyState == 4 && this.status == 200) {
                cf(this);
            }
        };
        xhttp.open("POST", "/basic-cli/play", true);
        xhttp.setRequestHeader("Content-type", "application/json");
        xhttp.send(JSON.stringify(playerMove));
    }

    moveSent(xhttp) {
        console.log(xhttp);
        const success = JSON.parse(xhttp.response).success;
        console.log(success);
        if (success) {
            this.setState({
                stagedMove: {source: null, tile: null, dest: null}
            });
        }
    }

    handleMoveChange(move: Move) {
        this.setState({
            stagedMove: move
        });
    }

    handleMoveSubmit() {
        // console.log(this.state.stagedMove);
        this.sendMove(this.state.stagedMove);
    }

    handlePlayerChange(event) {
        // console.log(true)
        const player = labelToNull(event.target.value)
        this.setState({
            myPlayer: player
        });

        if (player == null) {
            clearInterval(this.state.intervalID);
            this.setState({
                intervalID: null
            });
        }
        else if (this.state.intervalID == null) {
            const intervalID = setInterval(this.pollServer, updateInterval);
            this.setState({
                intervalID: intervalID
            });
        }

        this.pollServerPlayer(player);
    }

    render() {
        const update = debug ?
            (<label>Update:
                <button id="update" onClick={this.pollServer} disabled={this.state.myPlayer == null}>Update</button>
            </label>)
            : null
        return (
            <div id="game-rendering">
                <label>Player ID:
                <select name="dest" id="dest" value={nullToLabel(this.state.myPlayer)} onChange={this.handlePlayerChange}>
                        <option value={nullLabel}>Select:</option>
                        <option value="0">Player 0</option>
                        <option value="1">Player 1</option>
                    </select>
                </label><br />
                <label>State text:<br />
                <textarea id="state-text" value={this.state.gameState.stateText} readOnly rows={debug ? 21 : 19} cols={41}></textarea>
                <StatusMsg msg={this.state.status} type={this.state.statusType}/>
                {update}
                </label>
                    <GraphicalInterface move={this.state.stagedMove} handleMoveChange={this.handleMoveChange} handleMoveSubmit={this.handleMoveSubmit} input_disabled={this.state.myPlayer == null ? "disabled" : null}/>
                    <CLIInterface move={this.state.stagedMove} handleMoveChange={this.handleMoveChange} handleMoveSubmit={this.handleMoveSubmit} input_disabled={this.state.myPlayer == null ? "disabled" : null}/>
            </div>
        );
    }
}

ReactDOM.render(
    <Game />,
    document.getElementById("game")
);
