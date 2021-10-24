namespace Qrng {
    open Microsoft.Quantum.Intrinsic;

    operation SampleQuantumRandomNumberGenerator() : Result {
        use q = Qubit(); // Allocate a qubit.
        H(q);            // Put the qubit to superposition. It now has a 50% chance of being 0 or 1.
        let r = M(q);    // Measure the qubit value.
        Reset(q);
        return r;
    }
}

namespace Superposition {
    open Microsoft.Quantum.Intrinsic;     // for H
    open Microsoft.Quantum.Measurement;   // for MResetZ
    open Microsoft.Quantum.Canon;         // for ApplyToEach
    open Microsoft.Quantum.Arrays;        // for ForEach

    operation MeasureSuperposition() : Result {
        use q = Qubit();     // allocates qubit for use (automatically in |0>)
        H(q);                // puts qubit in superposition of |0> and |1>
        return MResetZ(q);   // measures qubit, returns result (and resets it to |0> before deallocation)
    }

    operation MeasureSuperpositionArray(n : Int) : Result[] {
        use qubits = Qubit[n];
        ApplyToEach(H, qubits); 
        return ForEach(MResetZ, qubits);    
    }
}
