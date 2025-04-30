const express = require('express');
const fs = require('fs');
const path = require('path');
const app = express();
const PORT = 5550;

const filePath = path.join(__dirname, 'deviceList.json');

app.use(express.json());
app.use(express.static(__dirname));

app.get('/devices', (req, res) => {
  const data = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  res.json(data);
});

app.post('/addOrUpdate', (req, res) => {
  let devices = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  const { ip, name, location } = req.body;
  const index = devices.findIndex(d => d.ip === ip);

  if (index !== -1) {
    devices[index] = { ip, name, location };
  } else {
    devices.push({ ip, name, location });
  }

  fs.writeFileSync(filePath, JSON.stringify(devices, null, 2));
  res.sendStatus(200);
});

app.post('/delete', (req, res) => {
  let devices = JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  devices.splice(req.body.index, 1);
  fs.writeFileSync(filePath, JSON.stringify(devices, null, 2));
  res.sendStatus(200);
});

app.listen(PORT, () => {
  console.log(`Server running at http://localhost:${PORT}`);
});
