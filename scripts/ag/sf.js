const jsforce = require("jsforce");
const dotenv = require("dotenv");
dotenv.config();

const conn = new jsforce.Connection({
  instanceUrl: process.env.INSTANCE_URL,
  accessToken: process.env.ACCESS_TOKEN
});

// Perform some action with the connection object
conn.query("SELECT Id, Name FROM Account", (err, res) => {
  if (err) {
    console.error(err);
  } else {
    console.log(res);
  }
});
