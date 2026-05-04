module.exports = {
  apps: [
    {
      name: "mini-adam-runner",
      script: "runner/main.py",
      interpreter: "/home/ichigo/alexandria/mini-adam/.venv/bin/python",
      cwd: "/home/ichigo/alexandria/mini-adam",
      env: { PORT: "4001" },
      out_file: "logs/runner.out.log",
      error_file: "logs/runner.err.log",
    },
    {
      name: "mini-adam-router",
      script: "router/main.py",
      interpreter: "/home/ichigo/alexandria/mini-adam/.venv/bin/python",
      cwd: "/home/ichigo/alexandria/mini-adam",
      env: { PORT: "4000", RUNNER_URL: "http://localhost:4001" },
      out_file: "logs/router.out.log",
      error_file: "logs/router.err.log",
    },
  ],
};
