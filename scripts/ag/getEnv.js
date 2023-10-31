const { exec } = require("child_process");
const fs = require("fs");

const command = "sf org display user --json";

exec(command, (error, stdout, stderr) => {
  if (error) {
    console.error(`Error executing command: ${error}`);
    return;
  }

  const jsonOutput = JSON.parse(stdout);
  const jsonResult = jsonOutput["result"];

  let envOutput = "";
  for (const key in jsonResult) {
    if (jsonResult.hasOwnProperty(key)) {
      // Convert key to upper camel case
      const camelKey = key
        .replace(/([a-z0-9]|(?=[A-Z]))([A-Z])/g, "$1_$2")
        .toUpperCase();
      envOutput += `${camelKey}=${jsonResult[key]}\n`;
    }
  }

  fs.writeFileSync(".env", envOutput);
});
