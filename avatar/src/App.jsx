import { Suspense, useEffect, useState } from "react";
import { Canvas, useThree } from "@react-three/fiber";

import Avatar from "./Avatar";
import Room from "./Room";


/*
 * CONFIGURAÇÃO DA CÂMARA FIXA
 */

function CameraSetup() {
  const { camera } = useThree();

  useEffect(() => {

    /*
     * POSIÇÃO DA CÂMARA
     *
     * X = esquerda / direita
     * Y = altura
     * Z = distância
     */

    camera.position.set(
      0,
      1,
      3.5
    );


    /*
     * PONTO PARA ONDE A CÂMARA OLHA
     */

    camera.lookAt(
      0,
      1,
      -0.4
    );


    camera.updateProjectionMatrix();

  }, [camera]);

  return null;
}



function App() {

  const [expression, setExpression] =
    useState("neutral");


  return (
    <div className="app">

      <Canvas
        className="scene"

        camera={{
          fov: 35,
          near: 0.1,
          far: 100,
        }}

        gl={{
          antialias: true,
        }}
      >

        {/* CÂMARA FIXA */}
        <CameraSetup />


        {/* LUZ AMBIENTE */}
        <ambientLight
          intensity={0.7}
        />


        {/* LUZ PRINCIPAL */}
        <directionalLight
          position={[4, 6, 4]}
          intensity={1.5}
        />


        {/* LUZ SECUNDÁRIA */}
        <pointLight
          position={[-3.2, 2.2, -1.5]}
          intensity={4}
          distance={5}
        />


        <Suspense fallback={null}>

          {/* COZINHA */}
          <Room />


          {/* BAGHDAD */}
          <Avatar
            expression={expression}
          />

        </Suspense>

      </Canvas>


      {/* CONTROLOS TEMPORÁRIOS */}
      <div className="controls">

        <button
          onClick={() =>
            setExpression("neutral")
          }
        >
          Neutral
        </button>

        <button
          onClick={() =>
            setExpression("happy")
          }
        >
          Happy
        </button>

        <button
          onClick={() =>
            setExpression("surprised")
          }
        >
          Surprised
        </button>

        <button
          onClick={() =>
            setExpression("thinking")
          }
        >
          Thinking
        </button>

      </div>

    </div>
  );
}


export default App;