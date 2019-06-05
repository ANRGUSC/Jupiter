import React, { Component } from 'react';
import axios from 'axios';
import './AppForm.css';

class AppForm extends Component {
  constructor() {
    super();
      this.state = {
        appPath: '',
        SCHEDULER: '',
        nodes: 
        {
          nodesNum: '',
          nodesDetails: '',
        },
        exec_profiler_info: '',
        network_profiler_info: '',
      };
      this.handleChange = this.handleChange.bind(this);
      this.handleNodesChange = this.handleNodesChange.bind(this);
      this.handleSubmit = this.handleSubmit.bind(this);
      this.handlePlot = this.handlePlot.bind(this);
      this.handleGetExecProfile = this.handleGetExecProfile.bind(this);
      this.handleGetNetworkProfile = this.handleGetNetworkProfile.bind(this);
  };

  handleChange(event) {
    const name = event.target.name;
    const value = event.target.value;
    this.setState((prevState) => ({
      ...prevState,
      [name]: value,
    }));
  };

  handleNodesChange(event) {
    event.preventDefault()

    const name = event.target.name;
    const value = event.target.value;
    this.setState((prevState) => ({
      ...prevState,
      nodes: {
        ...prevState.nodes, 
        [name]: value,
      },
    }));
  };

  handleSubmit(event) {
    event.preventDefault()

    const data = this.state;
    axios.post(`http://localhost:5000/data`, data)
    .then((res) => { 
      this.setState((state) => ({
        ...state,
        appPath: '',
        SCHEDULER: '',
        nodes: 
        {
          nodesNum: '',
          nodesDetails: '',
        },
      }));
    })
    .catch((err) => { console.log(err); });
  };

  handleGetExecProfile(event) {
    axios.post(`http://localhost:5000/execution_profile`, '')
    .then((res) => { 
      var processed_info = JSON.parse(res.data.exec_profiler_info);
      //array
      this.setState((state) => ({
        ...state,
        exec_profiler_info: processed_info,
      }))
    })
  }

  handlePlot(event) {
    axios.get("http://localhost:5000/plot")
  }

  handleGetNetworkProfile(event) {
    axios.get("http://localhost:5000/network_profile")
    .then((res) => { 
      var processed_info = JSON.parse(res.data.network_profiler_info)
      console.log(processed_info)
      this.setState((state) => ({
        ...state,
        network_profiler_info: processed_info,
      }))
    })
  }


  render() {

    // modified the data from exec profiler
    var exec_info_arr = this.state.exec_profiler_info;
    var exec_info = [];
    var node = ""
    for(var j = 0; j < exec_info_arr.length; j++) {
      var info = JSON.parse(exec_info_arr[j])
      for(var i in info) {
        if (i === "0") {
          node = info[i]
        } else{
          exec_info.push(node + "," + info[i])
        }
      }
    }

    var profiler_info_arr = this.state.network_profiler_info;

    return (
      <div className="appForm">

        <div className="config mb-4">
          <h4 className="mb-3">Config Parameters</h4>
          <div className="subtitle mb-3">
            Config parameters before the Jupiter deployment.
          </div>
          <form className="mb-3 w-50" onSubmit={this.handleSubmit}>
            <div className="input-group mb-3">
              <div className="input-group-prepend">
                <span className="input-group-text">App path:</span>
              </div>
              <input
                name="appPath"
                className="form-control"
                type="text"
                placeholder="Enter the app path (Like 'app_specific_files/network_monitoring_app')"
                required
                onChange={this.handleChange}
              />
            </div>

            <div className="input-group mb-3">
              <div className="input-group-prepend">
                <label className="input-group-text">Task mapper:</label>
              </div>
              <select defaultValue="Choose task mapper" name="SCHEDULER" onChange={this.handleChange}>
                <option defaultValue="" disabled hidden>Choose task mapper</option>
                <option value="0">HEFT</option>
                <option value="1">WAVE_RANDOM</option>
                <option value="2">WAVE_GREEDY</option>
                <option value="3">HEFT_MODIFIED</option>
              </select>
            </div>

            <div className="nodesInfo">
              <div className="input-group mb-3">
                <div className="input-group-prepend">
                  <span className="input-group-text">Number of nodes: </span>
                </div>
                <input
                  name="nodesNum"
                  className="form-control"
                  placeholder="Enter the number of nodes"
                  required
                  onChange={this.handleNodesChange}
                />
              </div>
              <div className="input-group mb-3">
                <div className="input-group-prepend">
                  <span className="input-group-text">Node information: </span>
                </div>
                <textarea
                  name="nodesDetails"
                  className="form-control"
                  rows="5"
                  placeholder="Enter the node information here.&#x0a;e.g  home master&#x0a;node2 usa-east-nodea&#x0a;node3 usa-west-nodeb"
                  required
                  onChange={this.handleNodesChange}
                />
              </div>
            </div>

            <div className="submit">
              <input
                type="submit"
                className="btn btn-outline-primary "
                value="Submit"
              />
            </div>
          </form>
        </div>

        <div className="mention mb-4">
          <h4 className="mb-3">Deploy Jupiter</h4>
          <div className="mb-2">
            Please deploy Jupiter according to documents <a href="https://jupiter.readthedocs.io/en/latest/Jdeploy.html">below</a>.
            <p className="mt-1">
              Note: Before you run deployment scripts, click on the "Get Plots" button below to see the real-time data in another page.
            </p>
          </div>
          <iframe src="https://jupiter.readthedocs.io/en/latest/Jdeploy.html" name="jupiterDocs" height="500" width="750"></iframe>
        </div>

        <div className="mqtt mb-4">
          <h4 className="mb-3">CIRCE Visualization</h4>
          <button className="btn btn-outline-primary mr-2" onClick={this.handlePlot}>Get Plots</button>
          <a href="http://localhost:5006">Please see plots in a new window by click on this link.</a>
          <div id='testPlot' className="bk-root"></div>
        </div>


        <div className="exec mb-4">
          <h4 className="mb-3">Run Execution Profiler</h4>
          <div className="subtitle mb-4">
            Click this to see the execution time of each task on each node and the amount of data it passes to its child tasks.
          </div>
          <div className="d-flex justify-content-start align-items-center">
            <button className="btn btn-outline-primary px-3" onClick={this.handleGetExecProfile}>Run</button>
            <div className="exec-table-wrapper ml-5">
              <table className="exec-table">
                <thead>
                  <tr>
                    <th scope="col">Node</th>
                    <th scope="col">Task</th>
                    <th scope="col">Time (sec)</th>
                    <th scope="col">Output_data (Kbit)</th>
                  </tr>
                </thead>
                { exec_info.length === 0 || exec_info === "The execute information for is not ready." ? (
                  <tbody>
                    <tr>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                    </tr>
                  </tbody>
                  ) : (
                  <tbody>
                  {
                    exec_info.map((item, key) => {
                      return <tr key={key}>
                          <th className="font-weight-normal">{item.split(",")[0]}</th>
                          <th className="font-weight-normal">{item.split(",")[1]}</th>
                          <th className="font-weight-normal">{item.split(",")[2]}</th>
                          <th className="font-weight-normal">{item.split(",")[3]}</th>
                        </tr>;
                      })
                  }
                  </tbody>
                    )
                  }
              </table>
            </div>
          </div>
        </div>


        <div className="network mb-4">
          <h4 className="mb-3">Get Network Statistics</h4>
          <div className="subtitle mb-4">
            Click this to see communication information of all links between nodes in the network.
            <br/>
            It will give the quadratic regression parameters of each link representing the corresponding communication cost.
          </div>
          <div className="d-flex justify-content-start align-items-center">
            <button className="btn btn-outline-primary px-3" onClick={this.handleGetNetworkProfile}>Run</button>
            <div className="profiler-table-wrapper ml-5">
              <table className="profiler-table">
                <thead>
                  <tr>
                    <th scope="col">Source Node</th>
                    <th scope="col">Source IP</th>
                    <th scope="col">Destination Node</th>
                    <th scope="col">Destination IP</th>
                    <th scope="col">Parameters</th>
                  </tr>
                </thead>
                { profiler_info_arr.length === 0 || profiler_info_arr === "The network information for is not ready." ? (
                  <tbody>
                    <tr>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                      <th className="font-weight-normal">N/A</th>
                    </tr>
                  </tbody>
                  ) : (
                  <tbody>
                  {
                    profiler_info_arr.map((item, key) => {
                      return <tr key={key}>
                          <th className="font-weight-normal">{item.split(",")[0].replace(/"/g, "")}</th>
                          <th className="font-weight-normal">{item.split(",")[1].replace(/"/g, "")}</th>
                          <th className="font-weight-normal">{item.split(",")[2].replace(/"/g, "")}</th>
                          <th className="font-weight-normal">{item.split(",")[3].replace(/"/g, "")}</th>
                          <th className="font-weight-normal">{item.split(",")[4].replace(/"/g, "")}</th>
                        </tr>;
                      })
                  }
                  </tbody>
                    )
                  }
              </table>
            </div>
          </div>
        </div>

      </div>
    )
  };
};

export default AppForm;