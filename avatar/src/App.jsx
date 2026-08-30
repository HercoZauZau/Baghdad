import { Suspense, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";

import Avatar from "./Avatar";

function App() {
  const [expression, setExpression] = useState("neutral");

  return (
    <div className="app">
      <Canvas
        className="scene"
        camera={{
          position: [0, 1.4, 3.5],
          fov: 35,
          near: 0.1,
          far: 100,
        }}
      >
        <ambientLight intensity={1.5} />

        <directionalLight
          position={[3, 5, 4]}
          intensity={2}
        />

        <Suspense fallback={null}>
          <Avatar expression={expression} />
        </Suspense>

        <OrbitControls target={[0, 1, 0]} />
      </Canvas>

      <div className="controls">
        <button onClick={() => setExpression("neutral")}>
          Neutral
        </button>

        <button onClick={() => setExpression("happy")}>
          Happy
        </button>

        <button onClick={() => setExpression("surprised")}>
          Surprised
        </button>

        <button onClick={() => setExpression("thinking")}>
          Thinking
        </button>
      </div>
    </div>
  );
}

export default App;