const formDetails = document.querySelector("#details");

formDetails.addEventListener("submit", async (event) => {
  event.preventDefault();
  const name = document.querySelector("#name").value;
  const roll = Number(document.querySelector("#roll").value);
  const branch = document.querySelector("#branch").value;
  let skills = document.querySelector("#skills").value;
  skills = skills.split(",").map((s) => s.trim());

  const data = { name, roll, branch, skills };
//   alert(JSON.stringify(data, null, 2));

  try {
    const response = await fetch("http://localhost:3000/api/data", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(data)
    });
    const result = await response.json();
    alert(result.message);
  } catch (err) {
    alert("Something went wrong");
    console.log(`Error : ${err}`);
  }
});
