import SpeechRecognitionPolyfill from 'speech-recognition-aws-polyfill'


const TranscribeDictaphone = () => {
    const recognition = new SpeechRecognitionPolyfill({
        IdentityPoolId: 'us-west-2:2965f100-0dd8-467c-b23e-aeeee8115949', // your Identity Pool ID
        region: 'us-west-2' // your AWS region
        })
    recognition.lang = 'en-US'; // add this to the config above instead if you want
    var transcript;
    recognition.onresult = function(event) {
        transcript  = event.results[0][0]
        console.log('Heard: ', transcript)
        }

    recognition.onerror = console.error


  return (
    <div>
      <button onClick={recognition.start()}>Start</button>
      <button onClick={recognition.stop()}>Stop</button>
      <p>{transcript}</p>
    </div>
  );
};
export default TranscribeDictaphone;