function HW(props) {
    return (
        <b>
            Hello, {props.person}!
        </b>
    )
}

ReactDOM.render(
    <HW person="React" />,
    document.getElementById("reactroot")
)