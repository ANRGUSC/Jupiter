import React, { Component } from 'react';

import AppForm from './components/AppForm';

class App extends Component {

  render() {
    return (
      <div className="App m-5">
        <h3 className="mb-3"> Jupiter User Interface  v1.0</h3>
        <div className="subtitle mb-4">
          This is a web application for Jupiter to let users set up the project parameters and show the statistics results from Jupiter.
        </div>
        <AppForm />
      </div>
    );
  }
}

export default App;

// export REACT_APP_URL=http://localhost