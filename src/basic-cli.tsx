// import React from "react";
// import ReactDOM, { render } from "react-dom";

const { Component } = React;  // Mysterious fix inspired by https://stackoverflow.com/a/50927095
const { render } = ReactDOM;

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

type Move = {
    source: number | null,
    tile: Tile | null,
    dest: number | null
}

function pollServer(): GameState {
    return {
        stateText: "NONE"
    }
}

abstract class GameInterface extends Component<{move: Move, handleMoveChange, handleMoveSubmit}, {}> {
    constructor(props) {
        super(props);
        this.handleChange = this.handleChange.bind(this);
        this.handleSubmit = this.handleSubmit.bind(this);
        this.disabledness = this.disabledness.bind(this);
    }

    abstract handleChange(event): void;

    handleSubmit(event): void {
        this.props.handleMoveSubmit();
        event.preventDefault();
    }

    disabledness(): any {
        return (this.props.move.source == null || this.props.move.tile == null || this.props.move.dest == null) ? "disabled" : null;
    }

}

class GraphicalInterface extends GameInterface {
    nullLabel = "-"
    labelToNull = (label) => (label === this.nullLabel ? null : label)
    nullToLabel = (value) => (value === null ? this.nullLabel : value)

    constructor(props) {
        super(props);
    }

    handleChange(event): void {
        const newMove = Object.assign({}, this.props.move, {[event.target.name]: this.labelToNull(event.target.value)});
        this.props.handleMoveChange(newMove);
    }

    render() {
        return (
            <form id="graphicalInput" onSubmit={this.handleSubmit}>
                <label>Source:
                    <select name="source" id="source" value={this.nullToLabel(this.props.move.source)} onChange={this.handleChange}>
                        <option value={this.nullLabel}>Select:</option>
                        <option value="0">Bench</option>
                        <option value="1">Batch 1</option>
                        <option value="2">Batch 2</option>
                        <option value="3">Batch 3</option>
                        <option value="4">Batch 4</option>
                        <option value="5">Batch 5</option>
                    </select>
                </label>
                <label>Tile type:
                    <select name="tile" id="tile" value={this.nullToLabel(this.props.move.tile)} onChange={this.handleChange}>
                        <option value={this.nullLabel}>Select:</option>
                        <option value="A">Azul</option>
                        <option value="B">Blaze</option>
                        <option value="C">Crimson</option>
                        <option value="D">Dusk</option>
                        <option value="E">Ether</option>
                    </select>
                </label>
                <label>Destination:
                    <select name="dest" id="dest" value={this.nullToLabel(this.props.move.dest)} onChange={this.handleChange}>
                        <option value={this.nullLabel}>Select:</option>
                        <option value="0">Floor</option>
                        <option value="1">Stage 1</option>
                        <option value="2">Stage 2</option>
                        <option value="3">Stage 3</option>
                        <option value="4">Stage 4</option>
                        <option value="5">Stage 5</option>
                    </select>
                </label>
                <label>Play:
                    <input type="submit" value="Submit" disabled={this.disabledness()}/>
                </label>
            </form>
        );
    }
}

class CLIInterface extends GameInterface {
    tokenSeparator = " ";
    nullLabel = "-";

    constructor(props) {
        super(props);
    }

    handleChange(event): void {
        console.log(event.target.value);
        const newMove = this.commandToMove(event.target.value);
        console.log(newMove);
        this.props.handleMoveChange(newMove);
    }

    handleSubmit(event): void {
        this.props.handleMoveSubmit();
        event.preventDefault();
    }

    moveToCommand(move: Move): string {
        let components: string[] = []
        if (move.source != null) {components.push(move.source.toString())}
        else if (move.tile != null || move.dest != null) {components.push(this.nullLabel)}
        if (move.tile != null) {components.push(move.tile)}
        else if (move.dest != null) {components.push(this.nullLabel)}
        if (move.dest != null) {components.push(move.dest.toString())}
        return components.join(this.tokenSeparator);

        // return nullToLabel(move.source)+" "+nullToLabel(move.tile)+" "+nullToLabel(move.dest);
    }

    commandToMove(command: string): Move {  // This should be made much prettier.
        const components: string[] = command.replace(/\s/g, "").split("");
        console.log(components);
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
            <form id="cliInput" onSubmit={this.handleSubmit}>
                <label>CLI:
                    <input type="text" id="cli" value={this.moveToCommand(this.props.move)} onChange={this.handleChange} />
                </label>
                <label>Play:
                    <input type="submit" value="Submit" disabled={this.disabledness()}/>
                </label>
            </form>
        );
    }

}

class Game extends Component<{}, {gameState: GameState, stagedMove: Move}> {
    constructor(props) {
        super(props);
        this.state = {
            gameState: pollServer(),
            stagedMove: {source: null, tile: null, dest: null}
        }
        this.handleMoveChange = this.handleMoveChange.bind(this)
        this.handleMoveSubmit = this.handleMoveSubmit.bind(this)
    }

    handleMoveChange(move: Move) {
        this.setState({
            stagedMove: move
        })
    }

    handleMoveSubmit() {
        console.log(this.state.stagedMove);
    }

    render() {
        return (
            <div id="gameRendering">
                <label htmlFor="stateText">State text:</label><br />
                <textarea id="stateText" defaultValue={this.state.gameState.stateText}></textarea><br />
                        <GraphicalInterface move={this.state.stagedMove} handleMoveChange={this.handleMoveChange} handleMoveSubmit={this.handleMoveSubmit}/>
                        <CLIInterface move={this.state.stagedMove} handleMoveChange={this.handleMoveChange} handleMoveSubmit={this.handleMoveSubmit}/>
            </div>
        );
    }
}

ReactDOM.render(
    <Game />,
    document.getElementById("game")
);
