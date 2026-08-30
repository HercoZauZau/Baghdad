import {
  useGLTF,
} from "@react-three/drei";


export default function Room() {

  const { scene } =
    useGLTF(
      "/models/modern_kitchen.glb"
    );


  return (

    <primitive

      object={scene}

      position={[
        -0.2,
        0.072,
        -2
      ]}

      rotation={[
        0,
        Math.PI / 2,
        0
      ]}

      scale={0.4}

    />

  );

}


useGLTF.preload(
  "/models/modern_kitchen.glb"
);