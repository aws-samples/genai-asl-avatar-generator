import React from "react";
import { API, Auth, Storage } from "aws-amplify";
import "./ASLForm.css";
import uuid from "react-uuid";
import IconButton from "@material-ui/core/IconButton";
import Tooltip from "@mui/material/Tooltip";
import { red } from "@material-ui/core/colors";

class ASLForm extends React.Component {
  textareaRef = React.createRef();
  constructor(props) {
    super(props);
    this.state = {
      value: "",
      signVideo: "",
      poseVideo: "",
      listening: false,
      letterCount: 0,
    };
    this.handleRecording = this.handleRecording.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.uploadFile = this.uploadFile.bind(this);
    var SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = new SpeechRecognition();
    this.recognition.onresult = (event) => {
      console.log("onresult");
      const transcript = event.results[0][0].transcript;
      this.setState({ value: transcript });
      console.log("transcript==" + transcript + "==");
      if (transcript !== "") {
        console.log("getvideos");
        this.getSignVideos({
          Text: transcript,
        });
      }
    };
  }

  handleChange = (event) => {
    const inputValue = event.target.value;
    const count = inputValue.replace(/[^a-zA-Z]/g, "").length;
    this.setState({ value: inputValue, letterCount: count });
  };

  handleRecording(event) {
    if (this.state.listening) {
      this.recognition.stop();
      this.setState({ listening: false });
      console.log("stopListening");
      event.preventDefault();
    } else {
      console.log("handleStartListening");
      this.recognition.start();
      this.setState({ value: "", listening: true });
      event.preventDefault();
    }
  }

  handleSubmit(event) {
    event.preventDefault();
    //call the API
    //this.getSignVideos(this.state.value);
    console.log("handleSubmit");
    this.getSignVideos({
      Text: this.state.value,
    });
  }

  async uploadFile(e) {
    const file = e.target.files[0];
    const keyName = uuid() + "/" + file.name;
    try {
      await Storage.put(keyName, file, {});
      this.getSignVideos({
        BucketName: "genasl-data",
        KeyName: "public/" + keyName,
      });
    } catch (error) {
      console.log("Error uploading file: ", error);
    }
  }

  async getSignVideos(queryStringParameters) {
    console.log(queryStringParameters);
    this.setState({signVideo:null,
      poseVideo:null })
    const apiName = "Audio2Sign";
    const path = "/sign";

    const myInit = {
      headers: {
        Authorization: `Bearer ${(await Auth.currentSession())
          .getIdToken()
          .getJwtToken()}`,
      },
      response: true, // OPTIONAL (return the entire Axios response object instead of only response.data)
      queryStringParameters: queryStringParameters,
    };

    console.log(myInit)

    const response = await API.get(apiName, path, myInit);
    console.log(response.data);

    this.setState({
      signVideo: response.data.SignURL,
      poseVideo: response.data.PoseURL,
    });

    // return response.data;
  }

  render() {
    return (
      <div>
        <section className="discover-section">
          <div className="translate-view">
            <div className="box">
              <div>
                <p className="box-header">English</p>
                <div
                  style={{
                    width: "100%",
                    height: 1,
                    backgroundColor: "#D0D5DD",
                  }}
                ></div>
              </div>
              <textarea
                ref={this.textareaRef}
                value={this.state.value}
                onChange={this.handleChange}
                className="text-area"
                style={{
                  outline: 0,
                  boxSizing: "border-box",
                  padding: 10,
                  border: 0,
                }}
              />
              <div className="box-setting">
                <div>
                  <p className="letter-count">{this.state.letterCount}/500</p>
                </div>
                <div className="function-comp">
                  <div className="translate-btn">
                    <Tooltip
                      title="Translate English to ASL"
                      className="button-tooltip"
                    >
                      <IconButton onClick={this.handleSubmit}>
                        <img
                          className="translate-img"
                          src={require("../assets/sign-language-green.png")}
                          alt="Translate Button"
                        />
                      </IconButton>
                    </Tooltip>
                  </div>
                  <div className="upload-btn">
                    <input
                      accept="audio/*"
                      id="icon-button-file"
                      type="file"
                      onChange={this.uploadFile}
                    />
                    <label htmlFor="icon-button-file">
                      <Tooltip title="Upload Audio" className="button-tooltip">
                        <IconButton
                          color="primary"
                          aria-label="upload audio"
                          component="span"
                        >
                          {/* <PhotoCamera /> */}
                          <img
                            className="upload-img"
                            src={require("../assets/upload-red.png")}
                            alt="Upload Button"
                          />
                        </IconButton>
                      </Tooltip>
                    </label>
                  </div>
                  <div className="speaker-btn">
                    <Tooltip
                      title={
                        this.state.listening ? "Stop Recording" : "Record Audio"
                      }
                      className="button-tooltip"
                    >
                      <IconButton onClick={this.handleRecording}>
                        <img
                          className="speaker-img"
                          src={
                            this.state.listening
                              ? require("../assets/stop-button.png")
                              : require("../assets/voice-blue.png")
                          }
                          alt="Speak Button"
                        />
                      </IconButton>
                    </Tooltip>
                  </div>
                </div>
              </div>
            </div>
            <div className="box">
              <div>
                <p className="box-header">Avatar</p>
                <div
                  style={{
                    width: "100%",
                    height: 1,
                    backgroundColor: "#D0D5DD",
                  }}
                ></div>
              </div>
              <div className="pose-video">
                <video
                  key={"pose" + this.state.poseVideo}
                  autoPlay
                  playsInline
                  loop
                  muted
                  style={{ width: "100%", height: "100%" }}
                >
                  <source src={this.state.poseVideo} />
                </video>
              </div>
            </div>
            <div className="box">
              <div>
                <p className="box-header">American Sign Language</p>
                <div
                  style={{
                    width: "100%",
                    height: 1,
                    backgroundColor: "#D0D5DD",
                  }}
                ></div>
              </div>
              <div className="sign-video">
                <video
                  key={"sign" + this.state.signVideo}
                  autoPlay
                  playsInline
                  loop
                  muted
                  style={{ width: "100%", height: "100%" }}
                >
                  <source src={this.state.signVideo} />
                </video>
              </div>
            </div>
          </div>
        </section>
      </div>
    );
  }
}

export default ASLForm;
