"""
Bias Detection and Mitigation Framework
Addresses: Bias and generalizability across scanners/vendors/protocols
Reference: Protocol Genome paper - Hidden confounders
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import json
from collections import Counter

sys.path.append(str(Path(__file__).parent))

class BiasAnalyzer:
    """
    Detect and mitigate bias from scanner/vendor differences
    Reference: Hidden confounders in medical imaging (arXiv)
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def analyze_dataset_bias(self, metadata_df: pd.DataFrame) -> Dict:
        """Comprehensive bias analysis"""
        
        print("\n" + "="*60)
        print("BIAS ANALYSIS")
        print("="*60)
        print("\nAnalyzing dataset for hidden confounders...")
        
        bias_report = {
            'total_samples': len(metadata_df),
            'manufacturer_distribution': {},
            'model_distribution': {},
            'protocol_diversity': 0,
            'site_imbalance': None,
            'recommendations': [],
            'risk_level': 'low',
            'bias_score': 0.0
        }
        
        # 1. Manufacturer distribution
        if 'manufacturer' in metadata_df.columns:
            mfg_dist = metadata_df['manufacturer'].value_counts()
            bias_report['manufacturer_distribution'] = mfg_dist.to_dict()
            
            # Check concentration
            max_concentration = mfg_dist.max() / len(metadata_df)
            
            if max_concentration > 0.8:
                bias_report['recommendations'].append(
                    "🔴 CRITICAL: Single manufacturer dominates (>80%). "
                    "Model will NOT generalize to other scanners."
                )
                bias_report['risk_level'] = 'critical'
                bias_report['bias_score'] += 0.4
            elif max_concentration > 0.6:
                bias_report['recommendations'].append(
                    "🟡 HIGH RISK: Manufacturer imbalance (>60%). "
                    "Consider data augmentation from other vendors."
                )
                if bias_report['risk_level'] == 'low':
                    bias_report['risk_level'] = 'high'
                bias_report['bias_score'] += 0.3
            elif max_concentration > 0.4:
                bias_report['recommendations'].append(
                    "🟡 MEDIUM RISK: Some manufacturer imbalance (>40%). "
                    "Use stratified sampling in train/test split."
                )
                if bias_report['risk_level'] == 'low':
                    bias_report['risk_level'] = 'medium'
                bias_report['bias_score'] += 0.2
        
        # 2. Model diversity
        if 'model' in metadata_df.columns:
            model_dist = metadata_df['model'].value_counts()
            bias_report['model_distribution'] = model_dist.head(10).to_dict()
            bias_report['unique_models'] = metadata_df['model'].nunique()
            
            if bias_report['unique_models'] < 3:
                bias_report['recommendations'].append(
                    "⚠️  LOW MODEL DIVERSITY: <3 scanner models. "
                    "Generalization will be limited."
                )
                bias_report['bias_score'] += 0.2
        
        # 3. Protocol diversity
        if 'protocol_name' in metadata_df.columns:
            bias_report['protocol_diversity'] = metadata_df['protocol_name'].nunique()
            
            if bias_report['protocol_diversity'] < 5:
                bias_report['recommendations'].append(
                    "⚠️  LOW PROTOCOL DIVERSITY: <5 unique protocols. "
                    "May not represent clinical variability."
                )
                bias_report['bias_score'] += 0.1
        
        # 4. Modality-specific checks
        if 'modality' in metadata_df.columns:
            for modality in metadata_df['modality'].unique():
                self._check_modality_specific_bias(
                    metadata_df[metadata_df['modality'] == modality],
                    modality,
                    bias_report
                )
        
        # 5. Calculate overall risk level
        if bias_report['bias_score'] > 0.6:
            bias_report['risk_level'] = 'critical'
        elif bias_report['bias_score'] > 0.4:
            bias_report['risk_level'] = 'high'
        elif bias_report['bias_score'] > 0.2:
            bias_report['risk_level'] = 'medium'
        
        # Print report
        self._print_bias_report(bias_report)
        
        # Save report
        report_path = self.output_dir / "bias_analysis_report.json"
        with open(report_path, 'w') as f:
            json.dump(bias_report, f, indent=2, default=str)
        print(f"\n✓ Bias report saved to: {report_path}")
        
        return bias_report
    
    def _check_modality_specific_bias(self, modal_df: pd.DataFrame, 
                                      modality: str, 
                                      bias_report: Dict):
        """Check for modality-specific biases"""
        
        if modality == 'CT':
            # Check slice thickness variation
            if 'slice_thickness' in modal_df.columns:
                st_values = modal_df['slice_thickness'].dropna()
                if not st_values.empty and len(st_values) > 1:
                    st_range = st_values.max() - st_values.min()
                    if st_range > 5.0:
                        bias_report['recommendations'].append(
                            f"⚠️  CT: Large slice thickness variation ({st_range:.1f}mm). "
                            "Consider resampling to common spacing."
                        )
                        bias_report['bias_score'] += 0.1
            
            # Check kVp variation
            if 'kvp' in modal_df.columns:
                kvp_values = modal_df['kvp'].dropna()
                if not kvp_values.empty:
                    kvp_unique = kvp_values.nunique()
                    if kvp_unique > 3:
                        bias_report['recommendations'].append(
                            f"⚠️  CT: High kVp variation ({kvp_unique} unique values). "
                            "May affect intensity calibration."
                        )
        
        elif modality == 'MR':
            # Check field strength variation
            if 'field_strength' in modal_df.columns:
                fs_values = modal_df['field_strength'].dropna()
                if not fs_values.empty:
                    fs_unique = fs_values.nunique()
                    if fs_unique > 2:
                        bias_report['recommendations'].append(
                            f"⚠️  MR: Multiple field strengths ({fs_unique}). "
                            "Consider separate models per field strength."
                        )
                        bias_report['bias_score'] += 0.15
    
    def _print_bias_report(self, report: Dict):
        """Print comprehensive bias report"""
        
        print("\n" + "="*60)
        print("BIAS REPORT")
        print("="*60)
        
        # Risk level
        risk_emoji = {
            'low': '🟢',
            'medium': '🟡',
            'high': '🟠',
            'critical': '🔴'
        }
        
        print(f"\n{risk_emoji.get(report['risk_level'], '⚪')} Risk Level: {report['risk_level'].upper()}")
        print(f"📊 Bias Score: {report['bias_score']:.2f} / 1.0")
        
        # Distribution summary
        print(f"\n📈 Dataset Composition:")
        print(f"  Total samples: {report['total_samples']}")
        
        if report['manufacturer_distribution']:
            print(f"\n  Manufacturer Distribution:")
            for mfg, count in sorted(report['manufacturer_distribution'].items(), 
                                    key=lambda x: x[1], reverse=True)[:5]:
                pct = count / report['total_samples'] * 100
                print(f"    • {mfg}: {count} ({pct:.1f}%)")
        
        if 'unique_models' in report:
            print(f"\n  Unique Scanner Models: {report['unique_models']}")
        
        if report['protocol_diversity'] > 0:
            print(f"  Unique Protocols: {report['protocol_diversity']}")
        
        # Recommendations
        if report['recommendations']:
            print(f"\n⚠️  RECOMMENDATIONS:")
            for i, rec in enumerate(report['recommendations'], 1):
                print(f"\n{i}. {rec}")
        else:
            print(f"\n✓ No significant bias detected")
    
    def stratified_sampling(self, metadata_df: pd.DataFrame, 
                          strata: List[str] = ['manufacturer', 'modality'],
                          test_size: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Create balanced train/test split across confounders
        Ensures representation from all scanner types
        """
        
        print("\n" + "="*60)
        print("STRATIFIED SAMPLING")
        print("="*60)
        print(f"\nStratifying by: {', '.join(strata)}")
        print(f"Test size: {test_size*100:.0f}%")
        
        try:
            from sklearn.model_selection import train_test_split
            
            # Create stratification column
            stratify_column = metadata_df[strata].astype(str).agg('-'.join, axis=1)
            
            # Split
            train, test = train_test_split(
                metadata_df,
                test_size=test_size,
                stratify=stratify_column,
                random_state=42
            )
            
            print(f"\n✓ Split complete:")
            print(f"  Train: {len(train)} samples")
            print(f"  Test: {len(test)} samples")
            
            # Verify balance
            print(f"\n📊 Distribution Check:")
            for stratum in strata:
                print(f"\n  {stratum}:")
                train_dist = train[stratum].value_counts(normalize=True)
                test_dist = test[stratum].value_counts(normalize=True)
                
                for value in train_dist.index:
                    train_pct = train_dist.get(value, 0) * 100
                    test_pct = test_dist.get(value, 0) * 100
                    print(f"    • {value}: Train={train_pct:.1f}%, Test={test_pct:.1f}%")
            
            return train, test
            
        except Exception as e:
            print(f"\n✗ Error in stratified sampling: {e}")
            print("Falling back to random split...")
            
            # Fallback: random split
            split_idx = int(len(metadata_df) * (1 - test_size))
            shuffled = metadata_df.sample(frac=1, random_state=42)
            return shuffled[:split_idx], shuffled[split_idx:]
    
    def recommend_mitigation_strategies(self, bias_report: Dict) -> List[str]:
        """Generate detailed mitigation strategies"""
        
        strategies = []
        
        if bias_report['risk_level'] in ['high', 'critical']:
            strategies.append(
                "🎯 PRIORITY 1: Data Augmentation\n"
                "   - Acquire data from underrepresented manufacturers\n"
                "   - Target at least 20% representation from each major vendor\n"
                "   - Use TCIA to find additional datasets"
            )
            
            strategies.append(
                "🎯 PRIORITY 2: Domain Adaptation\n"
                "   - Implement domain adversarial training\n"
                "   - Use scanner type as auxiliary task\n"
                "   - Apply histogram matching or CycleGAN for harmonization"
            )
        
        if bias_report['bias_score'] > 0.3:
            strategies.append(
                "🎯 Training Strategy:\n"
                "   - Use stratified K-fold cross-validation\n"
                "   - Report performance per manufacturer separately\n"
                "   - Monitor for scanner-specific overfitting"
            )
        
        strategies.append(
            "🎯 Validation Protocol:\n"
            "   - Test on held-out scanners (leave-one-scanner-out)\n"
            "   - Report confidence intervals per scanner type\n"
            "   - Track failure modes by equipment"
        )
        
        strategies.append(
            "🎯 Clinical Deployment:\n"
            "   - Validate on site-specific scanners before deployment\n"
            "   - Implement confidence thresholding per scanner\n"
            "   - Monitor performance drift in production"
        )
        
        print("\n" + "="*60)
        print("MITIGATION STRATEGIES")
        print("="*60)
        
        for i, strategy in enumerate(strategies, 1):
            print(f"\n{strategy}")
        
        # Save strategies
        strategies_path = self.output_dir / "mitigation_strategies.txt"
        with open(strategies_path, 'w') as f:
            f.write("\n\n".join(strategies))
        print(f"\n✓ Strategies saved to: {strategies_path}")
        
        return strategies


def main():
    """Run bias analysis"""
    
    print("\n" + "="*60)
    print("BIAS ANALYZER")
    print("="*60)
    print("\nAddresses: Bias and generalizability challenge")
    print("Reference: Protocol Genome - Hidden confounders (arXiv)")
    
    # Load protocol database if available
    protocol_db_path = Path("output/protocol_database.csv")
    
    if not protocol_db_path.exists():
        print("\n⚠️  Protocol database not found!")
        print("Please run 08_protocol_analyzer.py first")
        print("\nGenerating sample analysis...")
        
        # Create sample data for demonstration
        sample_data = pd.DataFrame({
            'manufacturer': ['SIEMENS'] * 15 + ['GE MEDICAL SYSTEMS'] * 3 + ['Philips'] * 2,
            'model': ['Sensation 64'] * 10 + ['Discovery'] * 5 + ['Brilliance'] * 5,
            'modality': ['CT'] * 12 + ['MR'] * 8,
            'protocol_name': ['Chest'] * 8 + ['Head'] * 6 + ['Spine'] * 6
        })
        
        analyzer = BiasAnalyzer()
        bias_report = analyzer.analyze_dataset_bias(sample_data)
        mitigation = analyzer.recommend_mitigation_strategies(bias_report)
        
    else:
        print(f"\n✓ Loading protocol database: {protocol_db_path}")
        metadata_df = pd.read_csv(protocol_db_path)
        
        analyzer = BiasAnalyzer()
        
        # Analyze bias
        bias_report = analyzer.analyze_dataset_bias(metadata_df)
        
        # Generate mitigation strategies
        mitigation = analyzer.recommend_mitigation_strategies(bias_report)
        
        # Demonstrate stratified sampling
        if len(metadata_df) > 10:
            print("\n" + "="*60)
            print("STRATIFIED SAMPLING DEMO")
            print("="*60)
            train, test = analyzer.stratified_sampling(metadata_df)
    
    print("\n" + "="*60)
    print("✓ BIAS ANALYSIS COMPLETE")
    print("="*60)
    print("\nResults saved to output/ directory")


if __name__ == "__main__":
    main()
