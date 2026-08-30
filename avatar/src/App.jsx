import {
  Suspense,
  useEffect,
  useState,
} from "react";

import {
  Canvas,
  useThree,
} from "@react-three/fiber";

import Avatar from "./Avatar";
import Room from "./Room";


function CameraSetup() {

  const { camera } = useThree();


  useEffect(() => {

    camera.position.set(
      0,
      1,
      3.5
    );


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

  const [
    expression,
    setExpression,
  ] = useState("neutral");


  const [
    text,
    setText,
  ] = useState(
    "Olá. O meu nome é Baghdad. É um prazer falar contigo."
  );


  const [
    speech,
    setSpeech,
  ] = useState(null);


  const [
    loading,
    setLoading,
  ] = useState(false);



  async function speak() {

    if (!text.trim()) {
      return;
    }


    setLoading(true);


    try {

      const response = await fetch(
        "http://127.0.0.1:8000/speak",
        {
          method: "POST",

          headers: {
            "Content-Type":
              "application/json",
          },

          body: JSON.stringify({
            text,
          }),
        }
      );


      if (!response.ok) {

        const error =
          await response.json();

        console.error(
          error
        );

        throw new Error(
          "Erro ao gerar fala."
        );

      }


      const data =
        await response.json();


      console.log(
        "Mouth cues:",
        data.mouthCues
      );


      setSpeech({
        audioUrl: data.audio,

        mouthCues:
          data.mouthCues,

        duration:
          data.duration,

        /*
         * Força nova reprodução
         * mesmo se o texto for igual.
         */
        id: Date.now(),
      });

    }

    catch (error) {

      console.error(
        error
      );


      alert(
        "Não foi possível gerar a fala."
      );

    }

    finally {

      setLoading(false);

    }

  }



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

        <CameraSetup />


        <ambientLight
          intensity={0.7}
        />


        <directionalLight
          position={[4, 6, 4]}
          intensity={1.5}
        />


        <pointLight
          position={[
            -3.2,
            2.2,
            -1.5,
          ]}
          intensity={4}
          distance={5}
        />


        <Suspense fallback={null}>

          <Room />


          <Avatar
            expression={expression}
            speech={speech}
          />

        </Suspense>

      </Canvas>



      <div className="tts-controls">

        <input

          value={text}

          onChange={(event) =>
            setText(
              event.target.value
            )
          }

          onKeyDown={(event) => {

            if (
              event.key === "Enter"
              &&
              !loading
            ) {

              speak();

            }

          }}

          placeholder="Escreve algo para a Baghdad..."

        />


        <button
          onClick={speak}
          disabled={loading}
        >

          {
            loading
              ? "A gerar..."
              : "Falar"
          }

        </button>

      </div>



      <div className="controls">

        <button
          onClick={() =>
            setExpression(
              "neutral"
            )
          }
        >
          Neutral
        </button>


        <button
          onClick={() =>
            setExpression(
              "happy"
            )
          }
        >
          Happy
        </button>


        <button
          onClick={() =>
            setExpression(
              "surprised"
            )
          }
        >
          Surprised
        </button>


        <button
          onClick={() =>
            setExpression(
              "thinking"
            )
          }
        >
          Thinking
        </button>

      </div>

    </div>

  );

}


export default App;