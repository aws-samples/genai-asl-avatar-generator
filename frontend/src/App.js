import { withAuthenticator } from "@aws-amplify/ui-react";
import "@aws-amplify/ui-react/styles.css";

import { Amplify, Auth } from "aws-amplify";
import awsconfig from "./aws-exports";
import "./App.css";
import ASLForm from "./components/ASLForm.js";

Amplify.configure(awsconfig);
Auth.configure(awsconfig);

function App({ signOut, user }) {
  return (
    <div class="main-container">
      <div class="main-container-header">
        <table>
          <tr>
            <td>
              <div class="gen-asl-logo">
                <img
                  src={require("./assets/gen-asl-logo.png")}
                  alt="gen-asl-logo"
                />
              </div>
            </td>
            <td>
              Generative AI Application To Produce American Sign Language
              Avatar
            </td>
          </tr>
        </table>
      </div>
      <div>&nbsp;</div>
      <ASLForm />
    </div>
  );
}
// export default App;
export default withAuthenticator(App);
