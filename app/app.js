const enrollAction = document.querySelector("#enrollAction");
const verifyAction = document.querySelector("#verifyAction");
const auditRows = document.querySelector("#auditRows");
const scoreValue = document.querySelector("#scoreValue");
const scoreMeter = document.querySelector("#scoreMeter");
const decisionBadge = document.querySelector("#decisionBadge");

function addAuditRow(eventName, subject, status) {
  const row = document.createElement("tr");
  row.innerHTML = `
    <td>${eventName}</td>
    <td>${subject}</td>
    <td>${status}</td>
  `;
  auditRows.prepend(row);
}

enrollAction.addEventListener("click", () => {
  addAuditRow("IdentityEnrolled", "subject-demo-001", "Confirmed");
  enrollAction.textContent = "Enrolled";
});

verifyAction.addEventListener("click", () => {
  const score = 0.78;
  scoreValue.textContent = score.toFixed(2);
  scoreMeter.style.width = `${score * 100}%`;
  decisionBadge.textContent = "Accepted";
  decisionBadge.classList.add("accepted");
  addAuditRow("VerificationLogged", "subject-demo-001", "Accepted");
});

