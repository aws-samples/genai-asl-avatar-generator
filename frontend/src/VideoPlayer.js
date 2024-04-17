import React from "react";

class Clip extends React.Component {
    constructor(props) {
        super(props);    
        this.state = {
            index: 0,
            videos: []
        };
        console.log('CLIP',this.state.index);
    }
    render(){
        return (
            <video key={this.state.videos[this.state.index]} autoPlay playsInline muted style={{ height: "20%", width: "20%" }} 
            onEnded={() => this.setState({ index: this.state.index + 1 })}
            >
            <source src={this.state.videos[this.state.index]} />
            </video>
        );
    }
}

export default Clip;
