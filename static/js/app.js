const demoRows = document.getElementById("demo-rows");
const errorEl = document.getElementById("error");
const resultsEl = document.getElementById("results");

const initialRows = [
  {
    name: "young_voters",
    baseline_voters: 12000,
    base_support_a: 55,
    elasticity: 0.2,
    turnout_delta: 600,
  },
  {
    name: "suburban_families",
    baseline_voters: 18000,
    base_support_a: 48,
    elasticity: 0.1,
    turnout_delta: 0,
  },
  {
    name: "retirees",
    baseline_voters: 9000,
    base_support_a: 42,
    elasticity: 0.15,
    turnout_delta: -300,
  },
];

const emptyRow = () => ({
  name: "",
  baseline_voters: 0,
  base_support_a: 50,
  elasticity: 0,
  turnout_delta: 0,
});

const createCellInput = (value, type = "number") => {
  const input = document.createElement("input");
  input.type = type;
  input.value = value;
  return input;
};

const addRow = (row) => {
  const tr = document.createElement("tr");
  const nameCell = document.createElement("td");
  const baseCell = document.createElement("td");
  const supportCell = document.createElement("td");
  const elasticityCell = document.createElement("td");
  const deltaCell = document.createElement("td");

  const nameInput = createCellInput(row.name, "text");
  const baseInput = createCellInput(row.baseline_voters);
  baseInput.min = 0;
  const supportInput = createCellInput(row.base_support_a);
  supportInput.min = 0;
  supportInput.max = 100;
  const elasticityInput = createCellInput(row.elasticity);
  const deltaInput = createCellInput(row.turnout_delta);

  nameCell.appendChild(nameInput);
  baseCell.appendChild(baseInput);
  supportCell.appendChild(supportInput);
  elasticityCell.appendChild(elasticityInput);
  deltaCell.appendChild(deltaInput);

  tr.appendChild(nameCell);
  tr.appendChild(baseCell);
  tr.appendChild(supportCell);
  tr.appendChild(elasticityCell);
  tr.appendChild(deltaCell);
  demoRows.appendChild(tr);
};

const renderRows = (rows) => {
  demoRows.innerHTML = "";
  rows.forEach(addRow);
};

const gatherPayload = () => {
  const rows = Array.from(demoRows.querySelectorAll("tr"));
  const demographics = [];
  const turnoutDelta = {};

  rows.forEach((row) => {
    const inputs = row.querySelectorAll("input");
    const name = inputs[0].value.trim();
    if (!name) {
      return;
    }
    const baseline = Number.parseInt(inputs[1].value, 10) || 0;
    const support = Number.parseFloat(inputs[2].value) || 0;
    const elasticity = Number.parseFloat(inputs[3].value) || 0;
    const delta = Number.parseInt(inputs[4].value, 10) || 0;

    demographics.push({
      name,
      baseline_voters: baseline,
      base_support_a: support,
      elasticity,
    });

    turnoutDelta[name] = delta;
  });

  return { demographics, turnout_delta: turnoutDelta };
};

const updateResults = (data) => {
  document.getElementById("baseline-total").textContent = data.baseline.total_voters;
  document.getElementById("scenario-total").textContent = data.scenario.total_voters;
  document.getElementById("swing-votes").textContent = data.vote_swing_a;
  document.getElementById("swing-share").textContent = `${data.share_swing_a.toFixed(2)} pts`;
  document.getElementById("baseline-share").textContent = `${data.baseline.share_a.toFixed(2)}%`;
  document.getElementById("scenario-share").textContent = `${data.scenario.share_a.toFixed(2)}%`;
  resultsEl.hidden = false;
};

document.getElementById("add-row").addEventListener("click", () => {
  addRow(emptyRow());
});

document.getElementById("reset").addEventListener("click", () => {
  renderRows(initialRows);
  resultsEl.hidden = true;
  errorEl.textContent = "";
});

document.getElementById("calculate").addEventListener("click", async () => {
  const payload = gatherPayload();
  if (!payload.demographics.length) {
    errorEl.textContent = "Please add at least one demographic row.";
    resultsEl.hidden = true;
    return;
  }

  try {
    const response = await fetch("/calculate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const message = await response.text();
      throw new Error(message || "Request failed");
    }

    const data = await response.json();
    errorEl.textContent = "";
    updateResults(data);
  } catch (error) {
    errorEl.textContent = error.message;
    resultsEl.hidden = true;
  }
});

renderRows(initialRows);
